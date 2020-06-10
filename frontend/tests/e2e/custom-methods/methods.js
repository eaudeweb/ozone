/* eslint-disable global-require */
/* eslint-disable import/no-extraneous-dependencies */
//  ? Unit: milliseconds
const delay = 100
//  ? Used to wait for elements css animation
const transitionDelay = 5 * delay
//  ? Used to wait for event action
const eventDelay = 5 * delay
//  ? Used to wait for cursor position
const moveToElementDelay = 2 * delay
//  ? Time in which element is expected to be visible
const elementVisibleTimeout = 200 * delay

const logMessage = (browser, message, header = false) => {
  const delimiter = header ? '===============' : '---------------'
  browser.perform((done) => {
    console.log(delimiter)
    console.log(message)
    console.log(delimiter)
    done()
  })
}

const logNetworkTraffic = (browser) => {
  browser.getLog('browser', logEntriesArray => {
    console.log('Network traffic')
    console.log(`Log length: ${logEntriesArray.length}`)
    logEntriesArray.forEach(log => {
      if (log.message.includes('api')) {
        const date = new Date(log.timestamp)
        console.log(`[${log.level}] ${date} : ${log.message}`)
      }
    })
  })
}

const hideFixedElements = (browser) => {
  browser
    .execute('document.querySelector(\'header.app-header\').style.display = \'none\'')
    .execute('document.querySelector(\'footer.app-footer\').style.display = \'none\'')
    .pause(delay)
}

const showFixedElements = (browser) => {
  browser
    .execute('document.querySelector(\'header.app-header\').style.display = \'inherit\'')
    .execute('document.querySelector(\'footer.app-footer\').style.display = \'inherit\'')
    .pause(delay)
}

const showMouse = (browser) => {
  browser
    .execute(() => {
      const app = document.getElementsByClassName('app')
      const cursor = document.createElement('div')
      cursor.setAttribute('id', 'cursor')
      app[0].appendChild(cursor)
      cursor.style.position = 'absolute'
      cursor.style.width = '20px'
      cursor.style.height = '20px'
      cursor.style.border = '2px solid #000'
      cursor.style.borderRadius = '50%'
      cursor.style.boxSizing = 'border-box'
      cursor.style.transform = 'translate(-50%, -50%)'
      cursor.style.pointerEvents = 'none'
      cursor.style.zIndex = '9999'
      document.addEventListener('mousemove', (e) => {
        const x = e.clientX
        const y = e.clientY

        cursor.style.left = `${x}px`
        cursor.style.top = `${y}px`
        cursor.style.borderColor = '#000'
      })
      // eslint-disable-next-line no-unused-vars
      document.addEventListener('click', (e) => {
        cursor.style.borderColor = 'red'
      })
      return true
    })
    .pause(10 * delay)
}

const login = (browser, username, password, mouse = false) => {
  logMessage(browser, `Log in with ${username}:${password}`)

  browser
    .url(process.env.VUE_DEV_SERVER_URL)
    .useXpath()
    .waitForElementVisible('//input[@id="id_username"]', elementVisibleTimeout)
    .waitForElementVisible('//input[@id="id_password"]', elementVisibleTimeout)
    .waitForElementVisible('//input[@type="submit"]', elementVisibleTimeout)
    .setValue('//input[@id="id_username"]', username)
    .pause(eventDelay)
    .setValue('//input[@id="id_password"]', password)
    .pause(eventDelay)
    .click('//input[@type="submit"]')
    .pause(eventDelay)
    .waitForElementNotPresent('//div[@class="api-action-display"]', 2 * elementVisibleTimeout)
    .waitForElementVisible('//div[contains(@class,"dashboard-page")]', elementVisibleTimeout)
    .assert.urlContains('/reporting/dashboard')

  if (mouse === true) {
    showMouse(browser)
  }
}

const logout = (browser) => {
  logMessage(browser, 'Log out', false)
  browser
    .useCss()
    .waitForElementVisible('header.app-header .navbar-nav a.dropdown-toggle', elementVisibleTimeout)
    .moveToElement('header.app-header .navbar-nav a.dropdown-toggle', undefined, undefined)
    .pause(moveToElementDelay)
    .click('header.app-header .navbar-nav a.dropdown-toggle')
    .pause(eventDelay)
    .waitForElementVisible('#logout_button', elementVisibleTimeout)
    .moveToElement('#logout_button', undefined, undefined)
    .pause(moveToElementDelay)
    .click('#logout_button')
    .pause(eventDelay)
    .waitForElementVisible('#id_username', elementVisibleTimeout)
    .assert.urlContains('/admin/login')
}

const setMultiSelector = (browser, selector_id, option, singleSelectWithText = true) => {
  let multiselectSingle = ''
  if (singleSelectWithText) {
    multiselectSingle = `//div[@id='${selector_id}']//span[contains(@class, 'multiselect__single') and contains(text(), '${option}')]`
  } else {
    multiselectSingle = `//div[@id='${selector_id}']//span[contains(@class, 'multiselect__single')]//span[contains(text(), '${option}')]`
  }
  browser
    .useXpath()
    /* Check if multiselect is visible */
    .waitForElementVisible(`//div[@id = '${selector_id}']//div[@class = 'multiselect']`, elementVisibleTimeout)
    .element('xpath', multiselectSingle, (result) => {
      if (result.status === -1) {
        browser
          /* Open multiselect */
          .moveToElement(`//div[@id = '${selector_id}']//div[@class = 'multiselect']`, undefined, undefined)
          .pause(moveToElementDelay)
          .click(`//div[@id = '${selector_id}']//div[@class = 'multiselect']`)
          .pause(eventDelay)
          /* Check if multiselect is opened */
          .waitForElementVisible(`//div[@id = '${selector_id}']//div[@class = 'multiselect__content-wrapper']`, elementVisibleTimeout)
          /* Check if desired option is visible */
          .waitForElementVisible(`//div[@id = '${selector_id}']//div[@class = 'multiselect__content-wrapper']//ul//li//span//span[contains(text(),'${option}')]`, elementVisibleTimeout)
          /* Select option */
          .moveToElement(`//div[@id = '${selector_id}']//div[@class = 'multiselect__content-wrapper']//ul//li//span//span[contains(text(),'${option}')]`, undefined, undefined)
          .pause(moveToElementDelay)
          .click(`//div[@id = '${selector_id}']//div[@class = 'multiselect__content-wrapper']//ul//li//span//span[contains(text(),'${option}')]`)
          .pause(eventDelay)
          /* Press escape if necessary */
          .keys(browser.Keys.ESCAPE)
          .pause(eventDelay)
      }
    })
}

const createSubmission = (browser, obligation, period, party, edit_party = false, back_to_dashboard = false) => {
  logMessage(browser, `Creating submission '${obligation}' for '${period}'`)
  const submission = {
    obligation_selector: { option: obligation, read_write: true, singleSelectWithText: true },
    period_selector: { option: period, read_write: true, singleSelectWithText: false },
    party_selector: { option: party, read_write: edit_party, singleSelectWithText: true }
  }
  browser
    .useXpath()
    .waitForElementVisible('//div[contains(@class, "create-submission")]', elementVisibleTimeout)
  for (const selector_id in submission) {
    if (submission[selector_id].read_write === true) {
      setMultiSelector(browser, selector_id, submission[selector_id].option, submission[selector_id].singleSelectWithText)
    }
  }
  browser
    .waitForElementVisible('//div[contains(@class,"create-submission")]//button', elementVisibleTimeout)
    .moveToElement('//div[contains(@class,"create-submission")]//button', undefined, undefined)
    .pause(moveToElementDelay)
    .click('//div[contains(@class,"create-submission")]//button')
    .pause(eventDelay)
    .waitForElementVisible("//div[@class='toasted bulma success' and contains(text(), 'Submission added successfully.')]", elementVisibleTimeout, false)
    .waitForElementNotPresent('//div[@class="api-action-display"]', 2 * elementVisibleTimeout)
    .waitForElementVisible("//div[@class='submission-info-tab']", 2 * elementVisibleTimeout)
  if (back_to_dashboard === true) {
    browser
      .waitForElementVisible("//a[@href='/reporting/dashboard' and contains(@class, 'nav-link')]", 2 * elementVisibleTimeout)
      .moveToElement("//a[@href='/reporting/dashboard' and contains(@class, 'nav-link')]", undefined, undefined)
      .pause(moveToElementDelay)
      .click("//a[@href='/reporting/dashboard' and contains(@class, 'nav-link')]")
      .pause(eventDelay)
  }
}

const handleModal = (browser, accept = true) => {
  const modal = "//div[@id='confirm-modal']"
  const acceptButton = "//button[contains(@class, 'btn-primary')]"
  const declineButton = "//button[contains(@class, 'btn-secondary')]"
  browser
    /* Check if moodal is opened */
    .useXpath()
    .waitForElementVisible(modal, elementVisibleTimeout)
  if (accept) {
    browser
      .waitForElementVisible(modal + acceptButton, elementVisibleTimeout)
      .click(modal + acceptButton)
      .pause(eventDelay)
  } else {
    browser
      .waitForElementVisible(modal + declineButton, elementVisibleTimeout)
      .click(modal + declineButton)
      .pause(eventDelay)
  }
}

const deleteSubmissionFake = (browser) => {
  logMessage(browser, 'Fake delete')
  browser
    .useXpath()
    .waitForElementVisible("//button[@id='delete-button']", elementVisibleTimeout)
    .click("//button[@id='delete-button']")
    .pause(eventDelay)
  handleModal(browser, false)
}
const deleteSubmission = (browser) => {
  browser
    .useXpath()
    .waitForElementVisible("//button[@id='delete-button']", elementVisibleTimeout)
    .click("//button[@id='delete-button']")
    .pause(eventDelay)
  handleModal(browser)

  /* Validation */
  browser
    .waitForElementVisible("//div[@class='toasted bulma success' and contains(text(), 'Submission deleted')]", elementVisibleTimeout)
    .waitForElementVisible("//table[@id='all-submissions-table']//div[contains(text(), 'There are no records to show')]", elementVisibleTimeout)
}

const saveSubmission = (browser, tabs = []) => {
  logMessage(browser, 'Saving submission')
  /* Enable edit mode if disabled */
  browser
    .useXpath()
    .element('xpath', '//footer[@class=\'app-footer\']//button[@id=\'edit-button\']', (result) => {
      if (result.status !== -1) {
        browser
          .click("//footer[@class='app-footer']//button[@id='edit-button']")
          .pause(eventDelay)
      }
    })
  browser
    .useXpath()
    /* Click Save and continue button */
    .execute('window.scrollTo(0,document.body.scrollHeight);')
    .pause(transitionDelay)
    .waitForElementVisible("//footer[@class='app-footer']//button[@id='save-button']", elementVisibleTimeout)
    .click("//footer[@class='app-footer']//button[@id='save-button']")
    .pause(eventDelay)
    .execute('document.body.scrollTop = 0;document.documentElement.scrollTop = 0')
  /* Check if desired tabs are valid */
  tabs.forEach(tab => {
    browser
      .waitForElementVisible(`//div[contains(@class,'form-wrapper')]//div[contains(@class, 'card-header')]//ul//li//div[contains(text(), '${tab}')]//i[contains(@class, 'fa-check-circle')]`, elementVisibleTimeout)
  })
  browser.waitForElementNotPresent('//div[@class="api-action-display"]', 2 * elementVisibleTimeout)
}

const selectTab = (browser, tab) => {
  hideFixedElements(browser)
  browser
    .useXpath()
    .execute('window.scrollTo(0,0)')
    .pause(transitionDelay)
    .waitForElementVisible(`//div[contains(@class, 'form-wrapper')]//div[contains(@class, 'card-header')]//ul//li//div[contains(text(), '${tab}')]`, elementVisibleTimeout)
    .click(`//div[contains(@class, 'form-wrapper')]//div[contains(@class, 'card-header')]//ul//li//div[contains(text(), '${tab}')]`)
    .pause(eventDelay)
  showFixedElements(browser)
}

const datePickerValue = (browser) => {
  const day = "//div[@id='date']//div[contains(@class, 'vdp-datepicker__calendar')][1]//span[contains(@class, 'cell day') and text()='1']"
  browser
    .moveToElement("//div[@id='date']//div[@class =  'vdp-datepicker']//input", undefined, undefined)
    .pause(moveToElementDelay)
    .waitForElementVisible("//div[@id='date']//div[@class =  'vdp-datepicker']//input", elementVisibleTimeout)
    .click("//div[@id='date']//div[@class =  'vdp-datepicker']//input")
    .pause(eventDelay)
    .waitForElementVisible(day, elementVisibleTimeout)
    .moveToElement(day, undefined, undefined)
    .pause(moveToElementDelay)
    .click(day)
    .pause(eventDelay)
}

const fillSubmissionInfo = (browser, submissionInfo = {}, autocomplet = true) => {
  logMessage(browser, 'Filling submission information')
  const fields = ['reporting_officer', 'designation', 'organization', 'postal_address', 'phone', 'email']
  /* Open Submission Info tab */
  selectTab(browser, 'Submission Information')
  browser
    .useXpath()
    .element('xpath', '//footer[@class=\'app-footer\']//button[@id=\'edit-button\']', (result) => {
      if (result.status !== -1) {
        browser
          .click("//footer[@class='app-footer']//button[@id='edit-button']")
          .pause(eventDelay)
      }
    })
  hideFixedElements(browser)
  browser
    .execute('window.scrollTo(0,document.body.scrollHeight);')
    .pause(transitionDelay)
    .waitForElementVisible("//input[@id='reporting_officer']", elementVisibleTimeout)
  fields.forEach(field => {
    /* Check if submissionInfo has missing fields */
    if (!submissionInfo.hasOwnProperty(field) && autocomplet) {
      submissionInfo[field] = ''
    }
    if (submissionInfo.hasOwnProperty(field)) {
      /* Add submissionInfo in input fields */
      if (field === 'postal_address') {
        browser
          .setValue(`//textarea[@id='${field}']`, submissionInfo[field])
          .pause(eventDelay)
      } else {
        browser
          .setValue(`//input[@id='${field}']`, submissionInfo[field])
          .pause(eventDelay)
      }
    }
  })
  /* Add country name (special case) */
  if (submissionInfo.country !== undefined) {
    browser
      .waitForElementVisible("//form[contains(@class,'form-sections')]//div[@class='multiselect']", elementVisibleTimeout)
      .click("//form[contains(@class,'form-sections')]//div[@class='multiselect']")
      .pause(eventDelay)
      .waitForElementVisible(`//div[@id='country']//span[contains(text(),'${submissionInfo.country}')]`, elementVisibleTimeout)
      .moveToElement(`//div[@id='country']//span[contains(text(),'${submissionInfo.country}')]`, undefined, undefined)
      .pause(moveToElementDelay)
      .click(`//div[@id='country']//span[contains(text(),'${submissionInfo.country}')]`)
      .pause(eventDelay)
  }
  /* Add date (special case) */
  datePickerValue(browser)
  showFixedElements(browser)
}

/**
 * 	saveAndFail(browser)
 *	Use this before calling clickQuestionnaireRadios(args)
 */
const saveAndFail = (browser, submissionInfo) => {
  logMessage(browser, 'Save and fail')

  fillSubmissionInfo(browser, submissionInfo)

  browser
    .useXpath()
    .execute('window.scrollTo(0,document.body.scrollHeight);')
    .pause(transitionDelay)
    .waitForElementVisible("//footer[@class='app-footer']//button[@id='save-button']", elementVisibleTimeout)
    .click("//footer[@class='app-footer']//button[@id='save-button']")
    .pause(eventDelay)
    .execute('document.body.scrollTop = 0;document.documentElement.scrollTop = 0')
    .pause(transitionDelay)
    .waitForElementVisible("//div[contains(@class,'form-wrapper')]//div[contains(@class, 'card-header')]//ul//li//div[contains(text(), 'Submission Information')]//i[contains(@class, 'fa-exclamation-circle')]", elementVisibleTimeout)
}
/**
 * 	editSubmission(browser)
 *	Must be in dashboard before using this function
 */
const editSubmission = (browser, table_order) => {
  browser
    .useXpath()
    .waitForElementVisible(`//table[@id='data-entry-submissions-table']//tbody//tr[${table_order}]//span[contains(text(), 'Edit')]`, elementVisibleTimeout)
    .click(`//table[@id='data-entry-submissions-table']//tbody//tr[${table_order}]//span[contains(text(), 'Edit')]`)
    .pause(eventDelay)
}

const openLookupTable = (browser, page) => {
  browser
    .useXpath()
    .execute('window.scrollTo(0,0)')
    .pause(transitionDelay)
    .waitForElementVisible(`//a[contains(@class, "nav-link") and contains(text(), '${page}')]`, elementVisibleTimeout)
    .moveToElement(`//a[contains(@class, "nav-link") and contains(text(), '${page}')]`, undefined, undefined, () => {
      browser
        .pause(moveToElementDelay)
        .useXpath()
        .click(`//a[contains(@class, "nav-link") and contains(text(), '${page}')]`)
        .pause(eventDelay)
        .waitForElementVisible('//div[contains(@class,"lookup-tables-page")]', 2 * elementVisibleTimeout)
        .moveToElement('//header[contains(@class, "app-header navbar")]//h3', 0, 0)
        .assert.urlContains('/reporting/lookup-tables')
        .waitForElementNotPresent('//div[@class="api-action-display"]', 2 * elementVisibleTimeout)
    })
}

const openDashboard = (browser) => {
  logMessage(browser, 'Opening Dashboard')
  let marginChanged = false
  browser.execute('window.getComputedStyle(document.querySelector("div.sidebar")).marginLeft === "-200px"', () => {
    browser.execute('document.querySelector("div.sidebar").style.marginLeft = "0"')
    marginChanged = true
  })
  browser
    .useXpath()
    .waitForElementVisible("//nav[contains(@class, 'sidebar-nav')]//a[@href='/reporting/dashboard' and contains(@class, 'nav-link')]", elementVisibleTimeout)
    .moveToElement("//nav[contains(@class, 'sidebar-nav')]//a[@href='/reporting/dashboard' and contains(@class, 'nav-link')]", undefined, undefined)
    .pause(moveToElementDelay)
    .click("//nav[contains(@class, 'sidebar-nav')]//a[@href='/reporting/dashboard' and contains(@class, 'nav-link')]")
    .pause(eventDelay)
    .waitForElementNotPresent('//div[@class="api-action-display"]', 2 * elementVisibleTimeout)
    .waitForElementVisible('//div[contains(@class,"dashboard-page")]', 2 * elementVisibleTimeout)
    .assert.urlContains('/reporting/dashboard')
  if (marginChanged) {
    browser.execute('document.querySelector("div.sidebar").style.marginLeft = ""')
  }
}

const openGeneralInstructions = (browser) => {
  logMessage(browser, 'Opening General Instructions')
  browser
    .useXpath()
    .waitForElementVisible("//button/i[contains(@class, 'fa-info')]", elementVisibleTimeout)
    .click("//button/i[contains(@class, 'fa-info')]")
    .pause(eventDelay)
    .execute('window.scrollTo(0,0)')
    .pause(transitionDelay)
    .click("//div[@id='instructions_modal']//header//button")
    .pause(eventDelay)
}

const openAsideMenu = (browser, tab) => {
  /* Toggler button */
  const aside_menu_toggler = `#${tab} .aside-menu .navbar-toggler-icon`
  /* Open aside menu if clossed */
  browser
    .useXpath()
    .execute('window.scrollTo(0,0)')
    .pause(transitionDelay)
    // eslint-disable-next-line no-unused-vars
    .execute(function getContent(data) {
      /* Convert the unicode of toggler icon to string */
      // eslint-disable-next-line prefer-rest-params
      return `\\u${getComputedStyle(document.querySelector(arguments[0]), ':before').content.replace(/'|"/g, '').charCodeAt(0).toString(16)}`
    }, [aside_menu_toggler], (result) => {
      const closed = '\\ue916'

      if (result.value === closed) {
        /* Open aside menu */
        browser
          .click(`//div[@id='${tab}']//aside[@class='aside-menu']//button[@class='navbar-toggler']`)
          .pause(eventDelay)
      }
    })
}

const closeAsideMenu = (browser, tab) => {
  browser
    .useXpath()
    .execute('window.scrollTo(0,0)')
    .pause(transitionDelay)
    .click(`//div[@id='${tab}']//aside[@class='aside-menu']//button[@class='navbar-toggler']`)
    .pause(eventDelay)
}

const filterSubmission = (browser, table, options, first_row_expected, rows_number_expected) => {
  logMessage(browser, 'Filtering submissions')
  const filters = {
    submission_search_filter: options[0],
    submission_obligation_filter: options[1],
    submission_party_filter: options[2],
    submission_from_filter: options[3],
    submission_to_filter: options[4]
  }
  browser
    .useXpath()
    .execute('window.scrollTo(0,document.body.scrollHeight);')
    .pause(transitionDelay)
    .waitForElementVisible('//button[contains(@id, "submission_clear_button")]', elementVisibleTimeout)
    .click('//button[contains(@id, "submission_clear_button")]')
    .pause(eventDelay)
  for (const filter in filters) {
    if (filters[filter] !== '') {
      browser
        .element('css selector', `input#${filter}`, (result) => {
          if (result.status !== -1) {
            browser
              .useCss()
              .setValue(`#${filter}`, filters[filter])
              .pause(eventDelay)
          } else {
            browser
              .useXpath()
              .moveTo(`//select[@id='${filter}']`, 0, 0)
              .pause(transitionDelay)
              .click(`//select[@id='${filter}']`)
              .pause(eventDelay)
              .click(`//select[@id='${filter}']//option[contains(text(), '${filters[filter]}')]`)
              .pause(eventDelay)
              /* Press escape if necessary */
              .keys(browser.Keys.ESCAPE)
              .pause(eventDelay)
          }
        })
    }
  }
  browser
    .useXpath()
    .execute('window.scrollTo(0,document.body.scrollHeight);')
    .pause(transitionDelay)

  first_row_expected.forEach((column_value, index) => {
    if (column_value !== '') {
      browser
        .waitForElementVisible(`//table[@id='${table}']//tbody//tr[1]//td[${index + 1}]//div[contains(text(), '${column_value}')]`, elementVisibleTimeout)
    }
  })
  browser
    .elements('css selector', `#${table} tbody tr`, (result) => {
      browser.assert.equal(`${result.value.length} rows`, `${rows_number_expected} rows`)
    })
    .pause(eventDelay)
}

const filterEntity = (browser, tab, filters) => {
  logMessage(browser, 'Filtering entities')
  const tabs = {
    controlled_substances: {
      fields: ['substances-group-filter', 'substances-name-filter', 'substances-formula-filter'],
      clear: 'substances-clear-button'
    },
    blends: {
      fields: ['blends-name-filter', 'blends-component-filter'],
      clear: 'blends-clear-button'
    },
    parties: {
      fields: ['parties-name-filter'],
      clear: ''
    }
  }
  browser.execute('window.scrollTo(0,0)').useCss()
  tabs[tab].fields.forEach((field, index) => {
    browser
      .useCss()
      .element('css selector', `#${field} .multiselect__select`, (result) => {
        if (result.status !== -1) {
          browser
            .click(`#${field}`)
            .pause(eventDelay)
            .waitForElementVisible(`#${field} .multiselect__content-wrapper`, elementVisibleTimeout)
            .useXpath()
            .click(`//div[@id='${field}']//div[@class='multiselect__content-wrapper']//ul//li//span//span[contains(text(),'${filters[index]}')]`)
            .pause(eventDelay)
            .keys(browser.Keys.ESCAPE)
            .pause(eventDelay)
            .waitForElementNotPresent('//div[@class="api-action-display"]', 2 * elementVisibleTimeout)
        } else {
          browser
            .setValue(`input#${field}`, filters[index])
            .pause(eventDelay)
            .waitForElementNotPresent('//div[@class="api-action-display"]', 2 * elementVisibleTimeout)
        }
      })
  })
  if (tabs[tab].clear !== '') {
    browser
      .useCss()
      .waitForElementVisible(`#${tabs[tab].clear}`, elementVisibleTimeout)
      .click(`#${tabs[tab].clear}`)
      .pause(eventDelay)
  }
}

const checkSumbissionInfoFlags = (browser) => {
  logMessage(browser, 'Checking submission info flags')
  browser
    .useXpath()
    .element('xpath', '//footer[@class=\'app-footer\']//button[@id=\'edit-button\']', (result) => {
      if (result.status !== -1) {
        browser
          .click("//footer[@class='app-footer']//button[@id='edit-button']")
          .pause(eventDelay)
      }
    })
  const flags = [
    'flag_has_reported_a1', 'flag_has_reported_a2',
    'flag_has_reported_b1', 'flag_has_reported_b2', 'flag_has_reported_b3',
    'flag_has_reported_c1', 'flag_has_reported_c2', 'flag_has_reported_c3',
    'flag_has_reported_e',
    'flag_has_reported_f'
  ]
  /* Open Submission Info tab */
  selectTab(browser, 'Submission Information')
  /* Check all flags */
  flags.forEach(flag => {
    browser
      .useCss()
      .getAttribute(`#${flag}`, 'checked', (result) => {
        if (result.value !== 'true') {
          browser
            .useXpath()
            .waitForElementVisible(`(//label[@for='${flag}'])[2]`, elementVisibleTimeout)
            .click(`(//label[@for='${flag}'])[2]`)
            .pause(eventDelay)
        }
      })
      .useCss()
      .expect.element(`#${flag}`).to.be.selected
  })
}

const clickQuestionnaireRadios = (browser, fields = [], allow_all = true) => {
  logMessage(browser, `Clicking questionnaire radios: ${fields}`)
  let restrictedFields = ['has_imports', 'has_exports', 'has_produced', 'has_destroyed', 'has_nonparty', 'has_emissions']
  const tabs = {
    has_imports: 'Imports',
    has_exports: 'Exports',
    has_produced: 'Production',
    has_destroyed: 'Destruction',
    has_nonparty: 'Non-Party',
    has_emission: 'Emission'
  }
  /* fields that will be set to 'yes' of no fields are given as argument */
  if (typeof fields !== 'undefined' && fields.length === 0 && allow_all === true) {
    fields = ['has_imports', 'has_exports', 'has_produced', 'has_destroyed', 'has_nonparty', 'has_emissions']
  }
  /* fields that will be set to 'no' */
  restrictedFields = restrictedFields.filter((e) => fields.indexOf(e) === -1)

  browser.useXpath()
  /* Enable edit mode if disabled */
  browser
    .element('xpath', '//footer[@class=\'app-footer\']//button[@id=\'edit-button\']', (result) => {
      if (result.status !== -1) {
        browser
          .click("//footer[@class='app-footer']//button[@id='edit-button']")
          .pause(eventDelay)
      }
    })
  /* Check if all tabs are disabled */
  for (const tab in tabs) {
    browser
      .waitForElementVisible(`//div[contains(@class,'form-wrapper')]//div[contains(@class, 'card-header')]//a[contains(@class, 'disabled')]//div[contains(text(), '${tabs[tab]}')]`, elementVisibleTimeout)
  }
  selectTab(browser, 'Questionnaire')
  hideFixedElements(browser)
  browser
    .waitForElementVisible("//div[contains(@class, 'form-wrapper')]//div[contains(@class, 'card-header')]//a[not(contains(@class, 'disabled'))]//div[contains(text(), 'Questionnaire')]", elementVisibleTimeout)
    .waitForElementVisible("//div[contains(@class, 'form-wrapper')]//div[contains(@class, 'card-header')]//a[not(contains(@class, 'disabled'))]//div[contains(text(), 'Files')]", elementVisibleTimeout)
    .waitForElementVisible("//div[contains(@class, 'form-wrapper')]//div[contains(@class, 'card-header')]//a[not(contains(@class, 'disabled'))]//div[contains(text(), 'Submission Information')]", elementVisibleTimeout)
    .waitForElementVisible("//div[contains(@class, 'form-wrapper')]//div[contains(@class, 'card-header')]//ul//li//div[contains(text(), 'Questionnaire')]", elementVisibleTimeout)
    .useCss()
    .execute('window.scrollTo(0,250);')
    .pause(transitionDelay)
    .waitForElementVisible('.field-wrapper #has_nonparty .custom-control:first-of-type label', elementVisibleTimeout)
  /* Set fields to 'yes' */
  for (const field of fields) {
    browser
      .moveToElement(`.field-wrapper #${field} .custom-control:first-of-type label`, undefined, undefined)
      .pause(moveToElementDelay)
      .click(`.field-wrapper #${field} .custom-control:first-of-type label`)
      .pause(eventDelay)
  }
  /* Set restrictedFields to 'no' */
  for (const restrictedField of restrictedFields) {
    browser
      .moveToElement(`.field-wrapper #${restrictedField} .custom-control:nth-of-type(2) label`, undefined, undefined)
      .pause(moveToElementDelay)
      .click(`.field-wrapper #${restrictedField} .custom-control:nth-of-type(2) label`)
      .pause(eventDelay)
  }
  showFixedElements(browser)
}

const addEntity = (browser, tab, entity, type, options, order = undefined, check = false) => {
  logMessage(browser, `Adding entity ${entity}: ${type} [${options}]`)
  const selectors = []
  /**
   * 	Entity structure
   * 	entity: [tab_name, option_1_selector, option_2_selector, submit_button, table_id]
   * 	ex -> substance: ['Substance', 'FII', 'HFC-23', 'add-substance-button', 'fii-table']
   */
  const entities = {
    'substance': ['Substance', 'substance_annex_selector', 'substance_selector', 'add-substance-button', 'substance-table'],
    'blend': ['Mixture', 'blend_type_selector', 'blend_selector', 'add-blend-button', 'blend-table']
  }
  /* Special case */
  // TODO: find a dynamic way
  if (type === 'F Hydrofluorocarbons (HFCs)') {
    entities.substance.pop()
    entities.substance.push('fii-table')
  }
  /* Correlate tabs with nav names and status column */
  const tabs_header = {
    has_imports_tab: { name: 'Imports' },
    has_exports_tab: { name: 'Exports' },
    has_produced_tab: { name: 'Production' },
    has_destroyed_tab: { name: 'Destruction' },
    has_nonparty_tab: { name: 'Non-Party' }
  }
  /* Get XPath of aside menu components	*/
  const aside_menu = `//div[@id='${tab}']//aside[@class='aside-menu']`
  const aside_nav = `${aside_menu}//div[@class='tabs']//ul[@class='nav nav-tabs']`
  /* Get XPath of entity selectors	*/
  selectors.push(`${aside_menu}//div[@class='tabs']//div[@id='${entities[entity][1]}']`)
  selectors.push(`${aside_menu}//div[@class='tabs']//div[@id='${entities[entity][2]}']`)
  const add_entity_button = `${aside_menu}//div[@class='tabs']//button[@id='${entities[entity][3]}']`
  /* Open desired tab */
  selectTab(browser, tabs_header[tab].name)
  /* Enable edit mode if disabled */
  browser
    .useXpath()
    .element('xpath', '//footer[@class=\'app-footer\']//button[@id=\'edit-button\']', (result) => {
      if (result.status !== -1) {
        browser
          .click("//footer[@class='app-footer']//button[@id='edit-button']")
          .pause(eventDelay)
      }
    })
  /* Open aside menu if clossed */
  openAsideMenu(browser, tab)
  browser
    .useXpath()
    /* Open entity form */
    .waitForElementVisible(`${aside_menu}//div[@class='tabs']`, elementVisibleTimeout)
    .waitForElementVisible(`${aside_nav}//span[contains(text(), '${entities[entity][0]}')]`, elementVisibleTimeout)
    .click(`${aside_nav}//span[contains(text(), '${entities[entity][0]}')]`)
    .pause(eventDelay)
  /* Add options type */
  browser
    .waitForElementVisible(selectors[0], elementVisibleTimeout)
    .moveToElement(selectors[0], undefined, undefined)
    .pause(moveToElementDelay)
    .click(selectors[0])
    .pause(eventDelay)
    .waitForElementVisible(`${selectors[0]}//div[@class='multiselect__content-wrapper']`, elementVisibleTimeout)
    .moveToElement(`${selectors[0]}//div[@class='multiselect__content-wrapper']//ul//li//span//span[text()='${type}']`, undefined, undefined)
    .pause(moveToElementDelay)
    .click(`${selectors[0]}//div[@class='multiselect__content-wrapper']//ul//li//span//span[text()='${type}']`)
    .pause(eventDelay)
  options.forEach(opt => {
    browser
      /* Add option */
      .waitForElementVisible(selectors[1], elementVisibleTimeout)
      .moveToElement(selectors[1], undefined, undefined)
      .pause(moveToElementDelay)
      .click(selectors[1])
      .pause(eventDelay)
      .waitForElementVisible(`${selectors[1]}//div[@class='multiselect__content-wrapper']`, elementVisibleTimeout)
      .moveToElement(`${selectors[1]}//div[@class='multiselect__content-wrapper']`, undefined, undefined)
      .pause(moveToElementDelay)
      .click(`${selectors[1]}//div[@class='multiselect__content-wrapper']//ul//li//span//span[text()='${opt}']`)
      .pause(eventDelay)
      /* Close selector */
      .sendKeys(`${selectors[1]}//div[@class='multiselect__content-wrapper']`, browser.Keys.ESCAPE)
      .pause(eventDelay)
  })
  /* Submit entity */
  browser
    .waitForElementVisible(add_entity_button, elementVisibleTimeout)
    .click(add_entity_button)
    .pause(eventDelay)

  closeAsideMenu(browser, tab)

  if (check === true) {
    hideFixedElements(browser)
    browser
      /* Check if entity was added and status is invalid */
      .waitForElementVisible(`//div[@id='${tab}']//table[@id='${entities[entity][4]}']//tbody//tr[${order}]//i[contains(@class, 'fa-exclamation-circle')]`, elementVisibleTimeout)
      .moveToElement(`//div[@id='${tab}']//table[@id='${entities[entity][4]}']//tbody//tr[${order}]//i[contains(@class, 'fa-exclamation-circle')]`, undefined, undefined)
      .pause(moveToElementDelay)
      .click(`//div[@id='${tab}']//table[@id='${entities[entity][4]}']//tbody//tr[${order}]//i[contains(@class, 'fa-exclamation-circle')]`)
      .pause(eventDelay)
      /* Check if Validation tab is opened and has a warrning */
      .waitForElementVisible(`${aside_menu}//div[@class='validation-tab']`, elementVisibleTimeout)
      .waitForElementVisible(`${aside_nav}//span[contains(@class, 'badge-danger')]`, elementVisibleTimeout)
      .execute('window.scrollTo(0,0)')
      .pause(transitionDelay)
    showFixedElements(browser)
    closeAsideMenu(browser, tab)
  }
}

const addFacility = (browser, table, tab, row, row_values, check = false) => {
  /* Open desired tab */
  selectTab(browser, 'Emissions')
  /* Enable edit mode if disabled */
  browser
    .useXpath()
    .element('xpath', '//footer[@class=\'app-footer\']//button[@id=\'edit-button\']', (result) => {
      if (result.status !== -1) {
        browser
          .click("//footer[@class='app-footer']//button[@id='edit-button']")
          .pause(eventDelay)
      }
    })
  hideFixedElements(browser)
  browser
    .useCss()
    .click('#add-facility-button')
    .pause(eventDelay)

  if (check === true) {
    browser
      .useXpath()
      .click(`//div[@id='has_emissions_tab']//table[@id='facility-table']//tbody//tr[${row}]//i[contains(@class, 'fa-exclamation-circle')]`)
      .pause(eventDelay)
    closeAsideMenu(browser, 'has_emissions_tab')
  }

  /* Add values to facility */
  for (const field_id of Object.keys(row_values)) {
    browser
      .useCss()
      .element('css selector', `#${tab} #${table} tbody tr:nth-child(${row}) textarea#${field_id}`, (result) => {
        if (result.status !== -1) {
          browser
            .setValue(`#${tab} #${table} tbody tr:nth-child(${row}) textarea#${field_id}`, row_values[field_id])
            .pause(eventDelay)
        } else {
          browser
            .setValue(`#${tab} #${table} tbody tr:nth-child(${row}) input#${field_id}`, row_values[field_id])
            .pause(eventDelay)
        }
      })
  }
  showFixedElements(browser)
}

const addValues = (browser, table, tab, row, row_values, modal_values, cell_order = 0) => {
  logMessage(browser, 'Adding values to entity')
  /* Enable edit mode if disabled */
  browser
    .useXpath()
    .element('xpath', '//footer[@class=\'app-footer\']//button[@id=\'edit-button\']', (result) => {
      if (result.status !== -1) {
        browser
          .click("//footer[@class='app-footer']//button[@id='edit-button']")
          .pause(eventDelay)
      }
    })
  hideFixedElements(browser)
  if (Object.entries(row_values).length > 0) {
    browser
      .useCss()
      .moveToElement(`#${tab} #${table} tbody tr:nth-child(${row})`, undefined, undefined)
      .pause(moveToElementDelay)
    /* Add values to entity */
    for (const field_id of Object.keys(row_values)) {
      browser
        .element('css selector', `#${tab} #${table} tbody tr:nth-child(${row}) textarea#tr_${cell_order}_${field_id}_${tab}`, (result) => {
          if (result.status !== -1) {
            browser
              .setValue(`#${tab} #${table} tbody tr:nth-child(${row}) textarea#tr_${cell_order}_${field_id}_${tab}`, row_values[field_id])
              .pause(eventDelay)
          } else {
            browser
              .setValue(`#${tab} #${table} tbody tr:nth-child(${row}) input#tr_${cell_order}_${field_id}_${tab}`, row_values[field_id])
              .pause(eventDelay)
          }
        })
    }
  }

  if (Object.entries(modal_values).length > 0) {
    /* Open edit modal */
    browser
      .waitForElementVisible(`#${tab} #${table} tbody tr:nth-child(${row}) td .fa-pencil-square-o`, elementVisibleTimeout)
      .moveToElement(`#${tab} #${table} tbody tr:nth-child(${row}) td .fa-pencil-square-o`, 10, 10)
      .pause(moveToElementDelay)
      .click(`#${tab} #${table} tbody tr:nth-child(${row}) td .fa-pencil-square-o`)
      .pause(eventDelay)

    browser
      .waitForElementVisible('#edit_modal .modal-body', elementVisibleTimeout)
    /* Add values in modal */
    for (const field_id of Object.keys(modal_values)) {
      browser
        .click(`#edit_modal .modal-body #tr_${cell_order}_${field_id}_${tab}`)
        .pause(eventDelay)
        .clearValue(`#edit_modal .modal-body #tr_${cell_order}_${field_id}_${tab}`)
        .setValue(`#edit_modal .modal-body #tr_${cell_order}_${field_id}_${tab}`, modal_values[field_id])
        .pause(eventDelay)
    }
    /* Close modal */
    browser
      .pause(eventDelay)
      .click('#edit_modal .modal-dialog button span[data-msgid="Close"]')
      .pause(eventDelay)
  }
  showFixedElements(browser)
}

const addComment = (browser, tab, comment) => {
  logMessage(browser, 'Adding comment')
  /* Enable edit mode if disabled */
  browser
    .useXpath()
    .element('xpath', '//footer[@class=\'app-footer\']//button[@id=\'edit-button\']', (result) => {
      if (result.status !== -1) {
        browser
          .click("//footer[@class='app-footer']//button[@id='edit-button']")
          .pause(eventDelay)
      }
    })
  browser
    .useCss()
    .setValue(`#${tab} .comments-input textarea`, comment)
    .pause(eventDelay)
}

// eslint-disable-next-line no-unused-vars
const rowIsEmpty = (browser, table, tab, row, row_values, modal_values, cell_order = 0) => {
  hideFixedElements(browser)
  browser
    .useCss()
    .moveTo(`#${tab} #${table} tbody tr:nth-child(${row})`)
    .pause(moveToElementDelay)
  /* Check if row is empty */
  for (const field_id of Object.keys(row_values)) {
    browser
      .element('css selector', `#${tab} #${table} tbody tr:nth-child(${row}) textarea#tr_${cell_order}_${field_id}_${tab}`, (result) => {
        if (result.status !== -1) {
          browser
            .getValue(`#${tab} #${table} tbody tr:nth-child(${row}) textarea#tr_${cell_order}_${field_id}_${tab}`, (data) => {
              browser.assert.equal(data.value, '')
            })
        } else {
          browser
            .getValue(`#${tab} #${table} tbody tr:nth-child(${row}) input#tr_${cell_order}_${field_id}_${tab}`, (data) => {
              browser.assert.equal(data.value, '')
            })
        }
      })
  }
  /* Open edit modal */
  browser.execute(`document.querySelector("#${tab} #${table} tbody tr:nth-child(${row})").classList.add("hovered")`, () => {
    browser
      .pause(transitionDelay)
      .click(`#${tab} #${table} tbody tr:nth-child(${row}) td .row-controls span:not(.table-btn)`)
      .pause(eventDelay)
  })
  browser
    .waitForElementVisible('#edit_modal .modal-body', elementVisibleTimeout)
    .pause(500)
  /* Check if modal inputs are empty */
  for (const field_id of Object.keys(modal_values)) {
    browser
      .getValue(`#edit_modal .modal-body #tr_${cell_order}_${field_id}_${tab}`, (data) => {
        browser.assert.equal(data.value, '')
      })
  }
  /* Close modal */
  browser
    .pause(eventDelay)
    .click('#edit_modal .modal-dialog .close')
    .pause(eventDelay)
    .execute(`document.querySelector("#${tab} #${table} tbody tr:nth-child(${row})").classList.remove("hovered")`, () => {})
  showFixedElements(browser)
}

const toggleMixtureDetails = (browser, table, tab, row) => {
  hideFixedElements(browser)
  browser
    .useCss()
    .waitForElementVisible(`#${tab} #${table} tbody tr:nth-child(${row}) td .substance-blend-cell`, elementVisibleTimeout)
    .click(`#${tab} #${table} tbody tr:nth-child(${row}) td .substance-blend-cell`)
    .pause(eventDelay)
    .waitForElementVisible(`#${tab} #${table} tr:nth-child(${row + 1}).b-table-details`, elementVisibleTimeout)
    .click(`#${tab} #${table} tbody tr:nth-child(${row}) td .substance-blend-cell`)
    .pause(eventDelay)
  showFixedElements(browser)
}

const uploadeFile = (browser, filename, filepath) => {
  logMessage(browser, 'Uploading file')
  const path = require('path')
  const find_root = require('find-root')
  const root = find_root(path.resolve(__dirname))
  const file = path.resolve(root + filename + filepath)
  browser
    .useCss()
    .waitForElementVisible('#choose-files-button__BV_file_outer_', elementVisibleTimeout)
    .setValue('input#choose-files-button', file, (result) => {
      if (result.status !== 0) {
        console.log(result)
      }
    })
    .pause(eventDelay)
}

module.exports = {
  logMessage,
  logNetworkTraffic,
  showMouse,
  login,
  logout,
  setMultiSelector,
  createSubmission,
  deleteSubmissionFake,
  deleteSubmission,
  saveSubmission,
  saveAndFail,
  editSubmission,
  selectTab,
  openLookupTable,
  openDashboard,
  openGeneralInstructions,
  openAsideMenu,
  closeAsideMenu,
  filterSubmission,
  filterEntity,
  fillSubmissionInfo,
  checkSumbissionInfoFlags,
  clickQuestionnaireRadios,
  addEntity,
  addFacility,
  addValues,
  addComment,
  rowIsEmpty,
  toggleMixtureDetails,
  uploadeFile
}
