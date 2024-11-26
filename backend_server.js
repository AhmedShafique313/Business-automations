const express = require('express');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

let tasks = [
  { id: 1, title: 'Sample Task', completed: false }
];

// Get all tasks
app.get('/api/tasks', (req, res) => {
  res.json(tasks);
});

// Create a new task
app.post('/api/tasks', (req, res) => {
  const newTask = { id: tasks.length + 1, ...req.body };
  tasks.push(newTask);
  res.status(201).json(newTask);
});

// Update a task
app.put('/api/tasks/:id', (req, res) => {
  const { id } = req.params;
  const taskIndex = tasks.findIndex(task => task.id === parseInt(id));
  if (taskIndex !== -1) {
    tasks[taskIndex] = { ...tasks[taskIndex], ...req.body };
    res.json(tasks[taskIndex]);
  } else {
    res.status(404).send('Task not found');
  }
});

// Delete a task
app.delete('/api/tasks/:id', (req, res) => {
  const { id } = req.params;
  tasks = tasks.filter(task => task.id !== parseInt(id));
  res.status(204).send();
});

const PORT = 5000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
