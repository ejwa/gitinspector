var PythonShell = require('python-shell');

var options = {
    // The main python script is in the same directory as this file
    scriptPath: __dirname,
    
    // Get command line arguments, skipping the default node args:
    // arg0 == node executable, arg1 == this file
    args: process.argv.slice(2)
};


// Set encoding used by stdin etc manually. Without this, gitinspector may fail to run.
process.env.PYTHONIOENCODING = 'utf8';

// Start inspector
var inspector = new PythonShell('gitinspector.py', options);

// Handle stdout
inspector.on('message', function(message) {
    console.log(message);
});

// Let the inspector run, catching any error at the end
inspector.end(function (err) {
    if (err) {
        throw err;
    }
});
