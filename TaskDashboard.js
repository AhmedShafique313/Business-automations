import React, { useEffect, useState } from 'react';
import axios from 'axios';

const TaskDashboard = () => {
    const [tasks, setTasks] = useState([]);

    useEffect(() => {
        const fetchTasks = async () => {
            try {
                const response = await axios.get('http://localhost:5000/api/tasks');
                setTasks(response.data);
            } catch (error) {
                console.error('Error fetching tasks:', error);
            }
        };

        fetchTasks();
    }, []);

    const createTask = async (title) => {
        try {
            const response = await axios.post('http://localhost:5000/api/tasks', { title, completed: false });
            setTasks([...tasks, response.data]);
        } catch (error) {
            console.error('Error creating task:', error);
        }
    };

    const updateTask = async (id, updatedTask) => {
        try {
            const response = await axios.put(`http://localhost:5000/api/tasks/${id}`, updatedTask);
            setTasks(tasks.map(task => (task.id === id ? response.data : task)));
        } catch (error) {
            console.error('Error updating task:', error);
        }
    };

    const deleteTask = async (id) => {
        try {
            await axios.delete(`http://localhost:5000/api/tasks/${id}`);
            setTasks(tasks.filter(task => task.id !== id));
        } catch (error) {
            console.error('Error deleting task:', error);
        }
    };

    return (
        <div>
            <h1>Task Dashboard</h1>
            <button onClick={() => createTask('New Task')}>Add Task</button>
            <ul>
                {tasks.map(task => (
                    <li key={task.id}>
                        {task.title}
                        <button onClick={() => updateTask(task.id, { ...task, completed: !task.completed })}>
                            {task.completed ? 'Mark Incomplete' : 'Mark Complete'}
                        </button>
                        <button onClick={() => deleteTask(task.id)}>Delete</button>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default TaskDashboard;
