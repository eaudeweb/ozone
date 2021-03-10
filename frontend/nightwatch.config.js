/* eslint-disable import/no-extraneous-dependencies */
/* eslint-disable global-require */
module.exports = {
  selenium: {
    start_process: true,
    server_path: process.env.OZONE_NIGHTWATCH_LOCAL_SELENIUM_JAR || require('selenium-server').path,
    host: '127.0.0.1',
    port: 4444,
    cli_args: {
      'webdriver.chrome.driver': process.env.OZONE_NIGHTWATCH_LOCAL_CHROMEDRIVER || require('chromedriver').path
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
