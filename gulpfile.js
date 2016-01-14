'use strict'

var _ = require('lodash');
var fs = require('fs');
var gulp = require('gulp');
var yaml = require('js-yaml');
var shell = require('shelljs');
var spawn = require('child_process').spawn;
var config = yaml.load(fs.readFileSync('config.yml')) || {};
var browsersync = require('browser-sync');
var watch = false;

// Default
gulp.task('default', function(callback) {
  shell.exec('gulp --tasks');
});

// Develop
gulp.task('develop', function(callback) {
    var sources = ['conductor/**', 'config.yml'];
    var command = 'DEBUG=1 python server.py';
    var server = helpers.spawn(command);
    setInterval(function () {
        if (!server) {
            server = helpers.spawn(command);
            setTimeout(browsersync.reload, 5000);
        }
    }, 1000);
    gulp.watch(sources, function(file) {
        if (server) process.kill(-server.pid);
        server = false;
    });
    process.on('SIGINT', function (code) {
        if (server) process.kill(-server.pid);
        process.exit();
    });
    browsersync.init(_.merge(config.browsersync, {
        proxy: 'localhost:' + config.port,
    }));
    callback();
});

// Start
gulp.task('start', function(callback) {
    var command = 'python server.py';
    shell.exec(command);
    callback();
});

// Helpers
var helpers = {
  spawn: function (command) {
    return spawn('sh', ['-c', command], {stdio: 'inherit', detached: true});
  },
};
