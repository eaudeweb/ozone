// http://nightwatchjs.org/gettingstarted#settings-file
/* eslint-disable import/no-extraneous-dependencies */
/* eslint-disable global-require */
module.exports = {
  src_folders: ['tests/e2e/specs'],
  output_folder: 'tests/e2e/reports',
  custom_assertions_path: ['tests/e2e/custom-assertions'],

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
      // desiredCapabilities: {
      //   browserName: 'chrome',
      //   javascriptEnabled: true,
      //   acceptSslCerts: true,
      //   chromeOptions: {
      //     args: [
      //       '--disable-dev-shm-usage',
      //       '--window-size=1800,900'
      //     ]
      //   }
      // },
      selenium_port: 4444,
      selenium_host: 'localhost',
      silent: true,
      skip_testcases_on_fail: false,
      end_session_on_fail: false
    },

    chrome: {
      desiredCapabilities: {
        browserName: 'chrome',
        javascriptEnabled: true,
        acceptSslCerts: true,
        chromeOptions: {
          args: [
            '--disable-dev-shm-usage',
            '--window-size=1800,900'
          ]
        }
      },
      skip_testcases_on_fail: false
    }
  }
}
