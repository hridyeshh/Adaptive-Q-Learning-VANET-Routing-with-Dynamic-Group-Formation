const express = require('express');
const path = require('path');
const app = express();
const port = 3000;

// Serve static files from the src/web/templates directory
app.use(express.static(path.join(__dirname, 'src/web/templates')));

// Route for the main page
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'src/web/templates/standalone.html'));
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
}); 