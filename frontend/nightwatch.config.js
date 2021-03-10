module.exports = {
  selenium: {
    start_process: true,
    server_path: process.env.OZONE_NIGHTWATCH_LOCAL_SELENIUM_JAR || './node_modules/selenium-server/lib/runner/selenium-server-standalone-3.141.59.jar',
    host: '127.0.0.1',
    port: 4444,
    cli_args: {
      'webdriver.chrome.driver': process.env.OZONE_NIGHTWATCH_LOCAL_CHROMEDRIVER || './node_modules/chromedriver/lib/chromedriver/chromedriver'
    }
  },

  test_settings: {
    default: {
      desiredCapabilities: {
        browserName: 'chrome',
        chromeOptions: {
          args: [
            '--headless',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--window-size=1800,900'
          ]
        },
        acceptSslCerts: true
      },
      skip_testcases_on_fail: false,
      end_session_on_fail: false
    }
  }
}
