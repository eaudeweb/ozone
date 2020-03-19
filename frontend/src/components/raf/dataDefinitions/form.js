import { getTabSubInfo } from '@/components/common/dataDefinitions/tabSubInfo'
import { setTabFiles } from '@/components/common/dataDefinitions/tabFiles'
import { getTabFlags } from '@/components/common/dataDefinitions/tabFlags'

// eslint-disable-next-line func-names && eslint-disable-next-line no-extend-native
const insetInArray = (index, item, arr) => {
  arr.splice(index, 0, item)
}

const getFormRaf = ($gettext) => {
  const form = {
    formDetails: {
      tabsDisplay: ['sub_info', 'files', 'essencrit'],
      dataNeeded: [
        'initialData.countryOptions',
        'initialData.countryOptionsSubInfo',
        'initialData.reportingChannel',
        'initialData.substances',
        'initialData.blends',
        'current_submission',
        'initialData.display.substances',
        'initialData.display.blends',
        'initialData.display.countries',
        'currentUser',
        'permissions.form',
        'submissionDefaultValues.reporting_channel',
        'initialData.approvedExemptionsList',
        'initialData.criticalUseCategoryList'
      ],
      comments_default_properties: {
        'raf_remarks_party': '',
        'raf_remarks_secretariat': ''
      },
      comments_endpoint_url: 'submission_remarks'
    },
    tabs: {
      sub_info: {
        ...getTabSubInfo($gettext),
        hideInfoButton: true,
        detailsHtml: $gettext('Respondents are requested to read the guidelines for reporting accounting framework of essential uses other than laboratory and analytical applications before proceeding and to refer to them as necessary when completing the data forms'),
        filterOut: ['submission_format']
      },
      ...setTabFiles($gettext),
      essencrit: {
        name: 'essencrit',
        hasAssideMenu: true,
        endpoint_url: 'raf_url',
        ordering_id: 0,
        status: null,
        validate: true,
        saving: false,
        formNumber: 2,
        title: $gettext('Essential and critical uses'),
        titleHtml: `<b>${$gettext('Reporting Accounting Framework')}</b><br><small>${$gettext('for essential and critical uses other than laboratory and analytical applications')}</small>`,
        detailsHtml: '',
        isInvalid: false,
        form_fields: [],
        blend_substance_headers: ['substance', 'percent', 'quantity_msac', 'quantity_sdac', 'quantity_dcpac'],
        get fields_order() {
          return this.section_subheaders.map(x => x.name)
        },
        get input_fields() {
          return this.section_subheaders.filter(x => x.isInput).map(x => x.name)
        },

        get modal_order() {
          const order = this.section_subheaders.map(x => x.name).filter(x => !['year', 'substance', 'validation'].includes(x))
          const indexImports = order.indexOf('quantity_import')
          insetInArray(indexImports, 'imports', order)
          const indexCritical = order.indexOf('quantity_used')
          insetInArray(indexCritical, 'critical_use_category', order)
          return order
        },
        section_subheaders: [{
          label: `A<br>${$gettext('Year')}`,
          name: 'year',
          colspan: 2
        }, {
          label: `B<br>${$gettext('Ozone depleting substances')}`,
          name: 'substance',
          colspan: 2
        }, {
          label: `C<br>${$gettext('Amount exempted')}`,
          name: 'quantity_exempted',
          isInput: true
        }, {
          label: `D<br>${$gettext('Amount acquired by production')}`,
          name: 'quantity_production',
          isInput: true
        }, {
          label: `E<br>${$gettext('Amount acquired by import & countries of manufacture')}`,
          name: 'quantity_import'
        }, {
          label: `F<br>${$gettext('Total acquired')} <br> (D+E)`,
          name: 'quantity_acquired',
          class: 'text-right'
        }, {
          label: `G<br>${$gettext('Authorized but not acquired')} <br> (C-F)`,
          name: 'quantity_authorized_not_acquired',
          class: 'text-right'
        }, {
          label: `H<br>${$gettext('On hand start of the year')}`,
          name: 'on_hand_start_year',
          isInput: true
        }, {
          label: `I<br>${$gettext('Available for use')}<br> (H+F)`,
          name: 'available_for_use',
          class: 'text-right'
        }, {
          label: `J<br>${$gettext('Amount used for essential use')}`,
          name: 'quantity_used',
          isInput: true
        }, {
          label: `K<br>${$gettext('Quantity contained in exported product')}`,
          name: 'quantity_exported',
          isInput: true
        }, {
          label: `L<br>${$gettext('Amount destroyed')}`,
          name: 'quantity_destroyed',
          isInput: true
        }, {
          label: `M<br>${$gettext('On hand end of year')}<br>(I-J-L)`,
          name: 'on_hand_end_year',
          class: 'text-right'
        }, {
          label: `<br>${$gettext('Emergency')}`,
          name: 'is_emergency',
          isInput: true
        }, {
          label: `<br>${$gettext('Actions')}`,
          name: 'validation'
        }],
        section_subheaders_critical: [{
          label: `A<br>${$gettext('Year')}`,
          name: 'year',
          colspan: 2
        }, {
          label: `B<br>${$gettext('Amount exempted')}`,
          name: 'quantity_exempted',
          isInput: true
        }, {
          label: `C<br>${$gettext('Amount acquired by production')}`,
          name: 'quantity_production',
          isInput: true
        }, {
          label: `D<br>${$gettext('Amount acquired by import & countries of manufacture')}`,
          name: 'quantity_import'
        }, {
          label: `E<br>${$gettext('Total acquired')} <br> (C+D)`,
          name: 'quantity_acquired',
          class: 'text-right'
        }, {
          label: `F<br>${$gettext('Authorized but not acquired')} <br> (B-E)`,
          name: 'quantity_authorized_not_acquired',
          class: 'text-right'
        }, {
          label: `G<br>${$gettext('On hand start of the year')}`,
          name: 'on_hand_start_year',
          isInput: true
        }, {
          label: `H<br>${$gettext('Available for use')}<br> (E+G)`,
          name: 'available_for_use',
          class: 'text-right'
        }, {
          label: `I<br>${$gettext('Amount used for critical use')}`,
          name: 'quantity_used',
          isInput: true
        }, {
          label: `J<br>${$gettext('Amount exported')}`,
          name: 'quantity_exported',
          isInput: true
        }, {
          label: `K<br>${$gettext('Amount destroyed')}`,
          name: 'quantity_destroyed',
          isInput: true
        }, {
          label: `L<br>${$gettext('On hand end of year')}<br>(H-I-J-K)`,
          name: 'on_hand_end_year',
          class: 'text-right'
        }, {
          label: `<br>${$gettext('Emergency')}`,
          name: 'is_emergency',
          isInput: true
        }, {
          label: `<br>${$gettext('Actions')}`,
          name: 'validation'
        }],
        section_headers: [{
          label: '',
          colspan: 17
        }
        ],
        comments: {
          raf_remarks_party: {
            name: 'raf_remarks_party',
            selected: '',
            type: 'textarea'
          },
          raf_remarks_secretariat: {
            name: 'raf_remarks_secretariat',
            selected: '',
            type: 'textarea'
          }
        },
        default_properties: {
          'imports': [],
          'remarks_party': '',
          'remarks_os': '',
          'quantity_exempted': null,
          'quantity_production': null,
          'quantity_used': null,
          'quantity_exported': null,
          'quantity_destroyed': null,
          'on_hand_start_year': null,
          'substance': null,
          'use_categories': [],
          'is_emergency': null
        }
      },
      flags: {
        ...getTabFlags($gettext),
        get fields_order() {
          return Object.keys(this.default_properties)
        },
        default_properties: {
          flag_provisional: false,
          flag_valid: null
        }
      }
    }
  }
  return form
}

export {
  getFormRaf
}
