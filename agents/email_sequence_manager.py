"""Manages automated email sequences and drip campaigns."""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import logging
from dataclasses import dataclass
from enum import Enum
from .email_manager import EmailManager
from .email_campaign_analytics import EmailAnalytics, VariantType

@dataclass
class SequenceStep:
    """Represents a step in an email sequence."""
    step_id: str
    template_id: Optional[int]
    subject: str
    content: str
    delay_days: int
    conditions: Dict[str, any] = None
    ab_test: bool = False
    variants: Dict[str, str] = None

class SequenceStatus(Enum):
    """Status of a contact in a sequence."""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    UNSUBSCRIBED = "unsubscribed"

@dataclass
class ContactSequenceState:
    """Tracks a contact's state within a sequence."""
    contact_id: str
    sequence_id: str
    current_step: int
    status: SequenceStatus
    last_email_date: datetime
    next_email_date: datetime
    engagement_metrics: Dict[str, int]
    custom_data: Dict[str, any]

class EmailSequenceManager:
    """Manages automated email sequences and drip campaigns."""
    
    def __init__(
        self,
        email_manager: EmailManager,
        analytics: EmailAnalytics,
        storage_path: str = "email_sequences.json"
    ):
        """Initialize sequence manager."""
        self.email_manager = email_manager
        self.analytics = analytics
        self.storage_path = storage_path
        self.sequences: Dict[str, List[SequenceStep]] = {}
        self.contact_states: Dict[str, ContactSequenceState] = {}
        self._setup_logging()
        self.load_sequences()
    
    def _setup_logging(self):
        """Set up logging configuration."""
        self.logger = logging.getLogger("EmailSequenceManager")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def load_sequences(self):
        """Load sequences and states from storage."""
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                self.sequences = data.get('sequences', {})
                states = data.get('contact_states', {})
                self.contact_states = {
                    k: ContactSequenceState(**v) for k, v in states.items()
                }
        except FileNotFoundError:
            self.logger.info(f"No existing sequences file found at {self.storage_path}")
    
    def save_sequences(self):
        """Save sequences and states to storage."""
        with open(self.storage_path, 'w') as f:
            json.dump({
                'sequences': self.sequences,
                'contact_states': {
                    k: v.__dict__ for k, v in self.contact_states.items()
                }
            }, f)
    
    def create_sequence(
        self,
        sequence_id: str,
        steps: List[SequenceStep]
    ) -> None:
        """Create a new email sequence."""
        if sequence_id in self.sequences:
            raise ValueError(f"Sequence {sequence_id} already exists")
        
        self.sequences[sequence_id] = steps
        self.logger.info(
            f"Created sequence {sequence_id} with {len(steps)} steps"
        )
        self.save_sequences()
    
    def add_contact_to_sequence(
        self,
        contact_id: str,
        sequence_id: str,
        custom_data: Dict[str, any] = None
    ) -> None:
        """Add a contact to an email sequence."""
        if sequence_id not in self.sequences:
            raise ValueError(f"Sequence {sequence_id} not found")
        
        state_key = f"{contact_id}_{sequence_id}"
        if state_key in self.contact_states:
            raise ValueError(
                f"Contact {contact_id} is already in sequence {sequence_id}"
            )
        
        self.contact_states[state_key] = ContactSequenceState(
            contact_id=contact_id,
            sequence_id=sequence_id,
            current_step=0,
            status=SequenceStatus.ACTIVE,
            last_email_date=datetime.now(),
            next_email_date=datetime.now(),
            engagement_metrics={
                'opens': 0,
                'clicks': 0,
                'replies': 0
            },
            custom_data=custom_data or {}
        )
        self.logger.info(
            f"Added contact {contact_id} to sequence {sequence_id}"
        )
        self.save_sequences()
    
    async def process_sequences(self):
        """Process all active sequences and send due emails."""
        now = datetime.now()
        tasks = []
        
        for state_key, state in self.contact_states.items():
            if (
                state.status == SequenceStatus.ACTIVE and
                state.next_email_date <= now and
                state.current_step < len(self.sequences[state.sequence_id])
            ):
                tasks.append(self.send_sequence_email(state_key))
        
        if tasks:
            await asyncio.gather(*tasks)
    
    async def send_sequence_email(self, state_key: str):
        """Send the next email in a sequence to a contact."""
        state = self.contact_states[state_key]
        sequence = self.sequences[state.sequence_id]
        step = sequence[state.current_step]
        
        try:
            # Handle A/B testing if enabled
            if step.ab_test and step.variants:
                variant_type = VariantType.CONTENT
                self.analytics.create_ab_test(
                    f"{state.sequence_id}_{step.step_id}",
                    variant_type,
                    step.variants
                )
                # Randomly select variant
                import random
                variant_name = random.choice(list(step.variants.keys()))
                content = step.variants[variant_name]
            else:
                content = step.content
            
            # Send email using email manager
            await self.email_manager.send_personalized_email(
                to_email=state.contact_id,  # Assuming contact_id is email
                to_name=state.custom_data.get('name', ''),
                subject=step.subject,
                html_content=content,
                template_id=step.template_id
            )
            
            # Update sequence state
            state.current_step += 1
            state.last_email_date = datetime.now()
            state.next_email_date = datetime.now() + timedelta(
                days=step.delay_days
            )
            
            if state.current_step >= len(sequence):
                state.status = SequenceStatus.COMPLETED
            
            self.save_sequences()
            self.logger.info(
                f"Sent sequence email {step.step_id} to {state.contact_id}"
            )
            
        except Exception as e:
            self.logger.error(
                f"Error sending sequence email to {state.contact_id}: {str(e)}"
            )
    
    def update_contact_engagement(
        self,
        contact_id: str,
        sequence_id: str,
        metric: str,
        value: int = 1
    ):
        """Update engagement metrics for a contact."""
        state_key = f"{contact_id}_{sequence_id}"
        if state_key not in self.contact_states:
            raise ValueError(
                f"Contact {contact_id} not found in sequence {sequence_id}"
            )
        
        state = self.contact_states[state_key]
        if metric in state.engagement_metrics:
            state.engagement_metrics[metric] += value
            self.save_sequences()
            
            # Update A/B test metrics if applicable
            sequence = self.sequences[sequence_id]
            step = sequence[state.current_step - 1]
            if step.ab_test:
                self.analytics.update_metrics(
                    f"{sequence_id}_{step.step_id}",
                    "variant_a",  # Need to track which variant was sent
                    metric
                )
    
    def get_sequence_performance(self, sequence_id: str) -> Dict:
        """Get performance metrics for a sequence."""
        if sequence_id not in self.sequences:
            raise ValueError(f"Sequence {sequence_id} not found")
        
        metrics = {
            'total_contacts': 0,
            'active_contacts': 0,
            'completed_contacts': 0,
            'total_opens': 0,
            'total_clicks': 0,
            'total_replies': 0,
            'step_performance': {}
        }
        
        for state in self.contact_states.values():
            if state.sequence_id == sequence_id:
                metrics['total_contacts'] += 1
                if state.status == SequenceStatus.ACTIVE:
                    metrics['active_contacts'] += 1
                elif state.status == SequenceStatus.COMPLETED:
                    metrics['completed_contacts'] += 1
                
                metrics['total_opens'] += state.engagement_metrics['opens']
                metrics['total_clicks'] += state.engagement_metrics['clicks']
                metrics['total_replies'] += state.engagement_metrics['replies']
        
        # Calculate step-specific metrics
        sequence = self.sequences[sequence_id]
        for i, step in enumerate(sequence):
            step_metrics = {
                'sent': 0,
                'opens': 0,
                'clicks': 0,
                'replies': 0
            }
            
            for state in self.contact_states.values():
                if (
                    state.sequence_id == sequence_id and
                    state.current_step > i
                ):
                    step_metrics['sent'] += 1
            
            if step.ab_test:
                ab_results = self.analytics.get_campaign_results(
                    f"{sequence_id}_{step.step_id}"
                )
                step_metrics.update({
                    'ab_test_results': ab_results
                })
            
            metrics['step_performance'][step.step_id] = step_metrics
        
        return metrics
