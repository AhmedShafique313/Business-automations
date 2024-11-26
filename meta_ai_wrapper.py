bothimport subprocess
import json
import os

class MetaAIWrapper:
    def __init__(self, credentials_path='/mnt/VANDAN_DISK/code_stuff/projects/experiments/credentials.json'):
        # Load credentials
        with open(credentials_path, 'r') as f:
            self.credentials = json.load(f)
        
        # Path to the Meta AI API directory
        self.meta_ai_path = '/mnt/VANDAN_DISK/code_stuff/projects/experiments/meta-ai-api'

    def generate_response(self, prompt):
        """
        Generate a response using Meta AI API
        
        :param prompt: The input prompt for the AI
        :return: AI-generated response
        """
        try:
            # Construct the command to run the Meta AI script
            command = [
                'node', 
                os.path.join(self.meta_ai_path, 'index.js'),
                prompt
            ]
            
            # Run the command and capture output
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                cwd=self.meta_ai_path
            )
            
            # Check for errors
            if result.returncode != 0:
                print(f"Error: {result.stderr}")
                return None
            
            # Return the generated response
            return result.stdout.strip()
        
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

# Example usage
if __name__ == "__main__":
    wrapper = MetaAIWrapper()
    response = wrapper.generate_response("Tell me about the future of AI")
    print(response)
