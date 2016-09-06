module.exports = (grunt) ->
  grunt.initConfig
    pkg: grunt.file.readJSON('package.json')
    sass:
      options:
        includePaths: [
          'node_modules'
        ]
      dist:
        files:
          'app/app.css': 'src/styles/main.scss'
    postcss:
      options:
        processors: [
          require('autoprefixer')({browsers: 'last 2 versions'})
        ]
      dist:
        src: 'app/app.css'
    browserify:
      dist:
        options:
          transform: ['babelify']
        files:
          'app/app.js': ['src/scripts/main.js']

    watch:
      scripts:
        files: ['src/scripts/**/*.js']
        tasks: ['browserify']
      style:
        files: ['src/styles/*.s?ss']
        # Skip postcss in dev YAGNI
        tasks: ['sass']

    browserSync:
      app:
        bsFiles:
          src: ['app/*.*', 'templates/**/*.html']
        options:
          watchTask: true
          proxy: "localhost:8080"

  grunt.loadNpmTasks 'grunt-sass'
  grunt.loadNpmTasks 'grunt-postcss'
  grunt.loadNpmTasks 'grunt-browserify'
  grunt.loadNpmTasks 'grunt-contrib-watch'
  grunt.loadNpmTasks 'grunt-browser-sync'

  grunt.registerTask 'default', ['build']
  grunt.registerTask 'dev', ['build', 'browserSync', 'watch']
  grunt.registerTask 'build', ['sass', 'postcss', 'browserify']
