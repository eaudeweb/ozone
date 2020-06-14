const getTabSubInfo = ($gettext) => {
  const tabSubInfo = {
    name: 'sub_info',
    hasAssideMenu: false,
    status: null,
    validate: true,
    endpoint_url: 'sub_info_url',
    endpoint_additional_url: '',
    fields_order: ['reporting_channel', 'submission_format', 'reporting_officer', 'designation', 'organization', 'postal_address', 'country', 'phone', 'email', 'date'],
    title: $gettext('Submission Information'),
    titleHtml: `<b>${$gettext('SUBMISSION INFORMATION')}</b><br><small>${$gettext('Please fill-in mandatory fields')}</small>`,
    detailsHtml: '',
    isInvalid: false,
    party: {
      label: $gettext('Party'),
      name: 'party',
      selected: 'China',
      type: 'text',
      validation: 'required',
      disabled: true
    },
    reporting_year: {
      label: $gettext('Reporting Period'),
      name: 'reporting_year',
      selected: '2016',
      type: 'text',
      validation: 'required',
      disabled: true
    },
    description: '',
    form_fields: {
      id: {
        selected: null
      },
      current_state: {
        selected: null
      },
      reporting_channel: {
        type: 'select',
        selected: '',
        optionsStatePropertyPath: 'initialData.reportingChannel',
        selectedPropertyPath: 'submissionDefaultValues.reporting_channel',
        options: []
      },
      reporting_officer: {
        type: 'text',
        selected: '',
        validation: null,
        description: $gettext('required')
      },
      designation: {
        type: 'text',
        selected: ''
      },
      organization: {
        type: 'text',
        selected: ''
      },
      postal_address: {
        type: 'textarea',
        selected: ''
      },
      country: {
        type: 'select',
        selected: '',
        optionsStatePropertyPath: 'initialData.countryOptionsSubInfo',
        options: []
      },
      submission_format: {
        type: 'select',
        selected: '',
        optionsStatePropertyPath: 'initialData.submissionFormats',
        selectedPropertyPath: 'submissionDefaultValues.submission_format',
        options: [],
        permission: 'is_secretariat'
      },
      phone: {
        type: 'text',
        selected: ''
      },
      email: {
        type: 'email-text',
        selected: '',
        validation: null,
        description: $gettext('required')
      },
      date: {
        type: 'date',
        selected: '',
        tooltip: $gettext('The date indicated on the submitted document')
      },
      submitted_at: {
        type: 'date',
        selected: '',
        validation: null,
        description: $gettext('required')
      },
      get validation() {
        const invalid = []
        if (this.current_state.selected === true) {
          if (!this.reporting_officer.selected) {
            this.reporting_officer.validation = $gettext('Required')
            invalid.push($gettext('Reporting officer'))
          } else {
            this.reporting_officer.validation = null
          }

          if (!this.email.selected) {
            this.email.validation = $gettext('Required')
            invalid.push($gettext('Email'))
          } else {
            this.email.validation = null
          }

          if (this.submitted_at.validation) {
            // This is a special case because this field is required only for secretariat users and validation property is set from outside
            invalid.push($gettext('Date submission'))
          }
        }

        return {
          selected: invalid
        }
      }
    },
    default_properties: {
      reporting_officer: null,
      id: null,
      designation: null,
      submission_format: null,
      organization: null,
      postal_address: null,
      country: null,
      phone: null,
      email: null,
      date: null,
      submitted_at: null,
      reporting_channel: null
    }
  }
  return tabSubInfo
}
export {
  getTabSubInfo
}
