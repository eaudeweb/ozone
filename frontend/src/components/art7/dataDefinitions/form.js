import { getTabSubInfo } from '@/components/common/dataDefinitions/tabSubInfo'
import { setTabFiles } from '@/components/common/dataDefinitions/tabFiles'
import { getTabFlags } from '@/components/common/dataDefinitions/tabFlags'
import { getQuestionnaireFields } from './questionnaireFields'

const getFormArt7 = ($gettext) => {
  const form = {
    formDetails: {
      tabsDisplay: ['sub_info', 'files', 'questionaire_questions', 'has_imports', 'has_exports', 'has_produced', 'has_destroyed', 'has_nonparty', 'has_emissions', 'flags'],
      dataNeeded: [
        'initialData.countryOptions',
        'initialData.substances',
        'initialData.blends',
        'current_submission',
        'initialData.display.substances',
        'initialData.display.blends',
        'initialData.display.countries',
        'initialData.reportingChannel',
        'initialData.countryOptionsSubInfo',
        'currentUser',
        'initialData.submissionFormats',
        'permissions.form',
        'submissionDefaultValues.reporting_channel',
        'submissionDefaultValues.submission_format'
      ],
      comments_default_properties: {
        imports_remarks_party: '',
        imports_remarks_secretariat: '',
        exports_remarks_party: '',
        exports_remarks_secretariat: '',
        production_remarks_party: '',
        production_remarks_secretariat: '',
        destruction_remarks_party: '',
        destruction_remarks_secretariat: '',
        nonparty_remarks_party: '',
        nonparty_remarks_secretariat: '',
        emissions_remarks_party: '',
        emissions_remarks_secretariat: '',
        questionnaire_remarks_party: '',
        questionnaire_remarks_secretariat: ''
      },
      comments_endpoint_url: 'submission_remarks'
    },
    tabs: {
      ...setTabFiles($gettext),
      sub_info: {
        ...getTabSubInfo($gettext),
        detailsHtml: $gettext('Respondents are requested to read the data reporting instructions and guidelines and to refer to them as necessary when completing the data forms.')
      },
      questionaire_questions: {
        name: 'questionaire_questions',
        hasAssideMenu: false,
        endpoint_url: 'article7questionnaire_url',
        title: $gettext('Questionnaire'),
        titleHtml: `<b>${$gettext('QUESTIONNAIRE')}</b> <br> <small>${$gettext('All answers are mandatory')}</small>`,
        detailsHtml: $gettext('Respondents are requested to read the Introduction, the General Instructions and the Definitions carefully before proceeding to the questionnaire.'),
        status: null,
        isInvalid: false,
        form_fields: getQuestionnaireFields($gettext),
        comments: {
          questionnaire_remarks_party: {
            selected: '',
            type: 'textarea'
          },
          questionnaire_remarks_secretariat: {
            selected: '',
            type: 'textarea'
          }
        },
        default_properties: {
          has_imports: false,
          has_exports: false,
          has_produced: false,
          has_destroyed: false,
          has_nonparty: false,
          has_emissions: false
        }
      },
      has_exports: {
        name: 'has_exports',
        hasAssideMenu: true,
        endpoint_url: 'article7exports_url',
        validate: true,
        status: null,
        saving: false,
        formNumber: 2,
        title: $gettext('Exports'),
        detailsHtml: $gettext('Fill in this form only if your country exported or re-exported CFCs, halons, carbon tetrachloride, methyl chloroform, HCFCs, HBFCs, bromochloromethane, methyl bromide or HFCs.'),
        titleHtml: `<b>${$gettext('EXPORTS')}</b> <br> <small>${$gettext('Annexes A, B, C, E and F substances')}</small> <br> <small>${$gettext('in metric tons (not ODP or CO₂-equivalent tonnes)')}</small>`,
        isInvalid: false,
        section_subheaders: [
          {
            label: `(1a) ${$gettext('Annex <br> Group')}`,
            name: 'group'
          },
          {
            label: `(1b) <br> ${$gettext('Substance')}`,
            name: 'substance'
          },
          {
            label: `(2) ${$gettext('Destination country/<br>region/territory')}`,
            name: 'destination_party'
          },
          {
            label: `(3) <br> ${$gettext('New')}`,
            name: 'quantity_total_new',
            width: 150
          },
          {
            label: `(4) ${$gettext('Recovered <br> and reclaimed')}`,
            name: 'quantity_total_recovered'
          },
          {
            label: `(5) <br> ${$gettext('Export for feedstock')}`,
            name: 'quantity_feedstock'
          },
          {
            label: `(6) <br> ${$gettext('Quantity')}`,
            name: 'quantity_exempted'
          },
          {
            label: `(7) <br> ${$gettext('Decision / type of use or remark')}`,
            name: 'decision_exempted',
            width: 200
          },
          {
            label: `<br> ${$gettext('Actions')}`,
            name: 'validation'
          }
        ],

        section_headers: [{
          label: ''
        },
        {
          label: ''
        },
        {
          label: ''
        },
        {
          label: '',
          tooltip: $gettext('Applicable to all substances, including those contained in mixtures and blends.')
        },
        {
          label: $gettext('Total Quantity Exported for All Uses'),
          colspan: 2
        },
        {
          label: '',
          tooltip: `${$gettext('Quantity of new substances exported as feedstock')} \n ${$gettext('Do not deduct from total production in column 3 of data form 3 (data on production).')}`
        },
        {
          label: $gettext('Quantity of new substance exported for exempted essential, critical, high-ambient-temperature or other uses'),
          colspan: 2,
          tooltip: $gettext('Against each substance exported for exempted essential, critical, high-ambient-temperature or other uses, please specify the Meeting of the Parties decision that approved the use.')
        },
        {
          label: ''
        }
        ],

        blend_substance_headers: ['substance', 'percent', 'quantity_total_new', 'quantity_total_recovered', 'quantity_feedstock', 'quantity_exempted'],

        fields_order: ['substance', 'blend', 'destination_party', 'quantity_total_new', 'quantity_total_recovered', 'quantity_feedstock', 'quantity_exempted', 'decision_exempted', 'validation'],
        hidden_fields_order: ['quantity_quarantine_pre_shipment', 'decision_quarantine_pre_shipment', 'quantity_laboratory_analytical_uses', 'decision_laboratory_analytical_uses', 'quantity_essential_uses', 'decision_essential_uses', 'quantity_critical_uses', 'decision_critical_uses', 'quantity_high_ambient_temperature', 'decision_high_ambient_temperature', 'quantity_process_agent_uses', 'decision_process_agent_uses', 'quantity_other_uses', 'decision_other_uses', 'quantity_polyols', 'decision_polyols'],
        modal_order: ['destination_party', 'quantity_total_new', 'quantity_total_recovered', 'quantity_feedstock'],
        form_fields: [],

        comments: {
          exports_remarks_party: {
            selected: '',
            type: 'textarea'
          },
          exports_remarks_secretariat: {
            selected: '',
            type: 'textarea'
          }
        },
        footnotes: [`[1] ${$gettext('Tonne = Metric ton.')}`],
        default_properties: {
          remarks_party: '',
          remarks_os: '',
          quantity_total_new: null,
          quantity_total_recovered: null,
          quantity_feedstock: null,
          quantity_critical_uses: null,
          decision_critical_uses: '',
          quantity_essential_uses: null,
          decision_essential_uses: '',
          quantity_high_ambient_temperature: null,
          decision_high_ambient_temperature: '',
          quantity_laboratory_analytical_uses: null,
          decision_laboratory_analytical_uses: '',
          quantity_process_agent_uses: null,
          decision_process_agent_uses: '',
          quantity_quarantine_pre_shipment: null,
          decision_quarantine_pre_shipment: '',
          destination_party: null,
          quantity_polyols: null,
          decision_polyols: null,
          substance: null,
          blend: null,
          decision: null
        }
      },
      has_imports: {
        name: 'has_imports',
        hasAssideMenu: true,
        endpoint_url: 'article7imports_url',
        status: null,
        validate: true,
        saving: false,
        formNumber: 1,
        title: $gettext('Imports'),
        titleHtml: `<b>${$gettext('IMPORTS')}</b> <br> <small>${$gettext('Annexes A, B, C, E and F substances')}</small> <br> <small>${$gettext('in metric tons (not ODP or CO₂-equivalent tonnes)')}</small>`,
        detailsHtml: $gettext('Fill in this form only if your country imported CFCs, halons, carbon tetrachloride, methyl chloroform, HCFCs, HBFCs, bromochloromethane, methyl bromide or HFCs.'),
        comments: {
          imports_remarks_party: {
            selected: '',
            type: 'textarea'
          },
          imports_remarks_secretariat: {
            selected: '',
            type: 'textarea'
          }
        },
        blend_substance_headers: ['substance', 'percent', 'quantity_total_new', 'quantity_total_recovered', 'quantity_feedstock', 'quantity_exempted'],
        section_subheaders: [{
          name: 'group',
          label: `(1) ${$gettext('Annex <br> Group')}`
        },
        {
          name: 'substance',
          label: `(2a) ${$gettext('Substance')}`
        },
        {
          name: 'source_party',
          label: `(2b) ${$gettext('Exporting country<br>/region/territory')}`
        },
        {
          label: `(3) <br> ${$gettext('New')}`,
          name: 'quantity_total_new',
          width: 150
        },
        {
          label: `(4) <br> ${$gettext('Recovered and reclaimed')}`,
          name: 'quantity_total_recovered'
        },
        {
          name: 'quantity_feedstock',
          label: `(5) <br> ${$gettext('Import for feedstock')}`
        },
        {
          label: `(6) <br> ${$gettext('Quantity')}`,
          name: 'quantity_exempted'
        },
        {
          label: `(7) <br> ${$gettext('Decision / type of use or remark')}`,
          name: 'decision_exempted',
          width: 200
        },
        {
          label: `<br> ${$gettext('Actions')}`,
          name: 'validation'
        }
        ],

        section_headers: [{
          label: ''
        },
        {
          label: ''
        },
        {
          label: ''
        },
        {
          label: '',
          tooltip: $gettext('Applicable to all substances, including those contained in mixtures and blends.')
        },
        {
          label: $gettext('Total Quantity Imported for All Uses'),
          colspan: 2
        },
        {
          label: '',
          tooltip: `${$gettext('Quantity of new substance imported for feedstock uses')} \n ${$gettext('Do not deduct from total production in column 3 of data form 3 (data on production).')}`
        },
        {
          label: $gettext('Quantity of new substance imported for exempted essential, critical, high-ambient-temperature or other uses'),
          colspan: 2,
          tooltip: $gettext('Against each substance imported for exempted essential, critical, high-ambient-temperature or other uses, please specify the Meeting of the Parties decision that approved the use.')
        },
        {
          label: ''
        }
        ],
        fields_order: ['substance', 'blend', 'source_party', 'quantity_total_new', 'quantity_total_recovered', 'quantity_feedstock', 'quantity_exempted', 'decision_exempted', 'validation'],
        hidden_fields_order: ['quantity_quarantine_pre_shipment', 'decision_quarantine_pre_shipment', 'quantity_laboratory_analytical_uses', 'decision_laboratory_analytical_uses', 'quantity_essential_uses', 'decision_essential_uses', 'quantity_critical_uses', 'decision_critical_uses', 'quantity_high_ambient_temperature', 'decision_high_ambient_temperature', 'quantity_process_agent_uses', 'decision_process_agent_uses', 'quantity_other_uses', 'decision_other_uses', 'quantity_polyols', 'decision_polyols'],
        modal_order: ['source_party', 'quantity_total_new', 'quantity_total_recovered', 'quantity_feedstock'],
        form_fields: [],
        isInvalid: false,
        footnotes: [`[1] ${$gettext('Tonne = Metric ton.')}`],
        default_properties: {
          remarks_party: '',
          remarks_os: '',
          quantity_total_new: null,
          quantity_total_recovered: null,
          quantity_feedstock: null,
          quantity_critical_uses: null,
          decision_critical_uses: '',
          quantity_essential_uses: null,
          decision_essential_uses: '',
          quantity_high_ambient_temperature: null,
          decision_high_ambient_temperature: '',
          quantity_laboratory_analytical_uses: null,
          decision_laboratory_analytical_uses: '',
          quantity_process_agent_uses: null,
          decision_process_agent_uses: '',
          quantity_quarantine_pre_shipment: null,
          decision_quarantine_pre_shipment: '',
          source_party: null,
          quantity_polyols: null,
          decision_polyols: null,
          substance: null,
          blend: null,
          decision: null
        }
      },
      has_produced: {
        name: 'has_produced',
        hasAssideMenu: true,
        endpoint_url: 'article7productions_url',
        status: null,
        validate: true,
        saving: false,
        formNumber: 3,
        title: $gettext('Production'),
        titleHtml: `<b>${$gettext('PRODUCTION AND HFC-23 GENERATION')}</b> <br><small> ${$gettext('in metric tons (not ODP or CO₂-equivalent tonnes)')}<br>${$gettext('Annex A, B, C, E and F substances')}</small>`,
        detailsHtml: $gettext('Fill in this form only if your country produced CFCs, halons, carbon tetrachloride, methyl chloroform, HCFCs, HBFCs, bromochloromethane, methyl bromide or HFCs or generated HFC-23.'),
        isInvalid: false,
        form_fields: [],
        fields_order: ['substance', 'blend', 'quantity_total_produced', 'quantity_feedstock', 'quantity_exempted', 'decision_exempted', 'quantity_article_5', 'validation'],
        special_fields_order: ['substance', 'quantity_total_produced', 'quantity_feedstock', 'quantity_for_destruction', 'quantity_exempted', 'decision_exempted', 'validation'],
        hidden_fields_order: ['quantity_quarantine_pre_shipment', 'decision_quarantine_pre_shipment', 'quantity_laboratory_analytical_uses', 'decision_laboratory_analytical_uses', 'quantity_essential_uses', 'decision_essential_uses', 'quantity_critical_uses', 'decision_critical_uses', 'quantity_high_ambient_temperature', 'decision_high_ambient_temperature', 'quantity_process_agent_uses', 'decision_process_agent_uses', 'quantity_other_uses', 'decision_other_uses'],
        modal_order: ['quantity_total_produced', 'quantity_feedstock', 'quantity_article_5'],
        blend_substance_headers: ['substance', 'percent', 'quantity_total_produced', 'quantity_feedstock', 'quantity_exempted', 'quantity_article_5'],
        section_subheaders: [
          {
            name: 'group',
            label: `(1) ${$gettext('Annex<br>Group')}`
          },
          {
            label: `(2) <br> ${$gettext('Substance')}`,
            name: 'substance'
          },
          {
            label: `(3) <br> ${$gettext('Total production for all uses')}`,
            name: 'quantity_total_produced',
            width: 150
          },
          {
            label: `(4) <br> ${$gettext('Production for feedstock uses within your country')}`,
            name: 'quantity_feedstock',
            width: 150
          },
          {
            label: `(5) <br> ${$gettext('Quantity')}`,
            name: 'quantity_exempted'
          },
          {
            label: `(6) <br> ${$gettext('Decision / type of use')}`,
            name: 'decision_exempted',
            width: 200
          },
          {
            label: `(7) <br> ${$gettext('Production for BDN for A5 Parties')}`,
            name: 'quantity_article_5'
          },
          {
            label: `<br> ${$gettext('Actions')}`,
            name: 'validation'
          }
        ],

        section_headers: [
          {
            label: ''
          },
          {
            label: ''
          },
          {
            label: ''
          },
          {
            label: ''
          },
          {
            label: ''
          },
          {
            label: $gettext('Production for exempted essential, critical or other uses within your country'),
            colspan: 2,
            tooltip: $gettext('Against each substance produced for exempted essential, critical or other uses, please specify the Meeting of the Parties decision that approved the use.')
          },
          {
            label: '',
            tooltip: $gettext('Production for supply to Article 5 countries in accordance with Articles 2A 2H and 5')
          },
          {
            label: ''
          }
        ],

        special_headers: {

          section_headers: [
            {
              label: ''
            },
            {
              label: ''
            },
            {
              label: '',
              tooltip: $gettext('HFC-23 generation that is captured, whether for destruction, feedstock or any other use, shall be reported in this form.')
            },
            {
              label: '',
              tooltip: $gettext('Amounts of HFC-23 captured for destruction or feedstock use will not be counted as production as per Article 1.'),
              colspan: 2
            },
            {
              label: $gettext('Production for exempted essential, critical or other uses within your country'),
              colspan: 2,
              tooltip: $gettext('Against each substance produced for exempted essential, critical or other uses, please specify the Meeting of the Parties decision that approved the use.')
            },
            {
              label: ''
            }
          ],

          section_subheaders: [
            {
              name: 'group',
              label: `(1) <br> ${$gettext('Annex/Group')}`
            },
            {
              label: `(2) <br> ${$gettext('Substance')}`,
              name: 'substance'
            },
            {
              label: `(3) <br> ${$gettext('Captured for all uses')}`,
              name: 'quantity_total_produced',
              width: 150
            },
            {
              label: `(4a) <br> ${$gettext('Captured for feedstock uses within your country')}`,
              name: 'quantity_feedstock',
              width: 150
            },
            {
              label: `(4b) <br> ${$gettext('Captured for destruction')}`,
              name: 'quantity_for_destruction'
            },
            {
              label: `(5) <br> ${$gettext('Quantity')}`,
              name: 'quantity_exempted'
            },
            {
              label: `(6) <br> ${$gettext('Decision / type of use')}`,
              name: 'decision_exempted',
              width: 200
            },
            {
              label: `(8) <br> ${$gettext('Actions')}`,
              name: 'validation'
            }
          ]
        },

        comments: {
          production_remarks_party: {
            selected: '',
            type: 'textarea'
          },
          production_remarks_secretariat: {
            selected: '',
            type: 'textarea'
          }
        },
        default_properties: {
          remarks_party: '',
          remarks_os: '',
          quantity_critical_uses: null,
          decision_critical_uses: '',
          quantity_essential_uses: null,
          decision_essential_uses: '',
          quantity_high_ambient_temperature: null,
          decision_high_ambient_temperature: '',
          quantity_laboratory_analytical_uses: null,
          decision_laboratory_analytical_uses: '',
          quantity_process_agent_uses: null,
          decision_process_agent_uses: '',
          quantity_quarantine_pre_shipment: null,
          decision_quarantine_pre_shipment: '',
          quantity_total_produced: null,
          quantity_feedstock: null,
          quantity_article_5: null,
          substance: null
        }
      },
      has_destroyed: {
        name: 'has_destroyed',
        hasAssideMenu: true,
        endpoint_url: 'article7destructions_url',
        status: null,
        validate: true,
        saving: false,
        formNumber: 4,
        title: $gettext('Destruction'),
        titleHtml: `<b>${$gettext('DESTRUCTION OF CONTROLLED SUBSTANCES')} </b> <br><small> ${$gettext('in metric tons (not ODP or CO₂-equivalent tonnes)<br>Annex A, B, C, E and F substances')}</small>`,
        detailsHtml: $gettext('Fill in this form only if your country destroyed CFCs, halons, carbon tetrachloride, methyl chloroform, HCFCs, HBFCs, bromochloromethane, methyl bromide or HFCs.'),
        fields_order: ['substance', 'quantity_destroyed', 'remarks_party', 'remarks_os', 'validation'],
        blend_substance_headers: ['substance', 'percent', 'quantity_destroyed'],
        modal_order: ['quantity_destroyed'],
        isInvalid: false,
        form_fields: [],
        section_subheaders: [{
          label: `(1a) ${$gettext('Annex <br> Group')}`,
          name: 'group'
        },
        {
          label: `(1b) ${$gettext('Substance')}`,
          name: 'substance'
        },
        {
          label: `(2) ${$gettext('Quantity destroyed')}`,
          name: 'quantity_destroyed'
        },
        {
          label: `(3a) ${$gettext('Remarks (party)')}`,
          name: 'remarks_party'
        },
        {
          label: `(3b) ${$gettext('Remarks (secretariat)')}`,
          name: 'remarks_os'
        },
        {
          label: `${$gettext('Actions')}`,
          name: 'validation'
        }
        ],

        default_properties: {
          remarks_party: '',
          remarks_os: '',
          quantity_destroyed: null,
          substance: null,
          blend: null
        },
        comments: {
          destruction_remarks_party: {
            selected: '',
            type: 'textarea'
          },
          destruction_remarks_secretariat: {
            selected: '',
            type: 'textarea'
          }
        }
      },
      has_nonparty: {
        name: 'has_nonparty',
        hasAssideMenu: true,
        endpoint_url: 'article7nonpartytrades_url',
        status: null,
        validate: true,
        saving: false,
        formNumber: 5,
        title: $gettext('Non-Party'),
        titleHtml: `<b>${$gettext('IMPORTS FROM AND/OR EXPORTS TO NON-PARTIES')} </b> <br><small> ${$gettext('in metric tons (not ODP or CO₂-equivalent tonnes)')}<br>${$gettext('Annex A, B, C and E substances')}</small>`,
        detailsHtml: $gettext('Fill in this form only if your country imported or exported CFCs, halons, carbon tetrachloride, methyl chloroform, HCFCs, HBFCs, bromochloromethane or methyl bromide from or to non-parties.'),
        isInvalid: false,
        fields_order: ['substance', 'blend', 'trade_party', 'quantity_import_new', 'quantity_import_recovered', 'quantity_export_new', 'quantity_export_recovered', 'remarks_party', 'remarks_os', 'validation'],
        modal_order: ['trade_party', 'quantity_import_new', 'quantity_import_recovered', 'quantity_export_new', 'quantity_export_recovered'],
        blend_substance_headers: ['substance', 'percent', 'quantity_import_new', 'quantity_import_recovered', 'quantity_export_new', 'quantity_export_recovered'],
        form_fields: [],
        section_subheaders: [{
          label: `(1) ${$gettext('Annex <br> Group')}`,
          name: 'group'
        },
        {
          label: `(2) <br> ${$gettext('Substance')}`,
          name: 'substance'
        },
        {
          label: `(3) ${$gettext('Exporting or destination <br> country/region/territory')}`,
          name: 'trade_party'
        },
        {
          label: `(4) <br> ${$gettext('New imports')}`,
          name: 'quantity_import_new'
        },
        {
          label: `(5) ${$gettext('Recovered and <br> reclaimed imports')}`,
          name: 'quantity_import_recovered'
        },
        {
          label: `(6) <br> ${$gettext('New exports')}`,
          name: 'quantity_export_new'
        },
        {
          label: `(7) <br> ${$gettext('Recovered and <br> reclaimed exports')}`,
          name: 'quantity_export_recovered'
        },
        {
          label: `(8a) <br> ${$gettext('Remarks (party)')}`,
          name: 'remarks_party'
        },
        {
          label: `(8b) <br> ${$gettext('Remarks (Secretariat)')}`,
          name: 'remarks_os'
        },
        {
          label: `<br> ${$gettext('Actions')}`,
          name: 'validation'
        }
        ],

        section_headers: [
          {
            label: ''
          },
          {
            label: ''
          },
          {
            label: ''
          },
          {
            label: '',
            tooltip: 'Exporting country/party/territory for quantities reported as imports OR country/party/territory of destination of exports'
          },
          {
            label: $gettext('Quantity of imports from non-parties'),
            colspan: 2,
            tooltip: $gettext('See definition of “non-parties” in Instruction V.')
          },
          {
            label: $gettext('Quantity of exports to non-parties'),
            colspan: 2,
            tooltip: $gettext('See definition of “non-parties” in Instruction V.')
          },
          {
            label: ''
          },
          {
            label: ''
          },
          {
            label: ''
          }
        ],

        comments: {
          nonparty_remarks_party: {
            selected: '',
            type: 'textarea'
          },
          nonparty_remarks_secretariat: {
            selected: '',
            type: 'textarea'
          }
        },
        default_properties: {
          remarks_party: '',
          remarks_os: '',
          quantity_import_new: null,
          quantity_import_recovered: null,
          quantity_export_new: null,
          quantity_export_recovered: null,
          substance: null,
          blend: null,
          trade_party: null
        }
      },
      has_emissions: {
        name: 'has_emissions',
        hasAssideMenu: false,
        endpoint_url: 'article7emissions_url',
        ordering_id: 0,
        status: null,
        validate: true,
        saving: false,
        formNumber: 6,
        title: $gettext('Emissions'),
        titleHtml: `<b>${$gettext('EMISSIONS OF HFC-23 FROM FACILITIES MANUFACTURING ANNEX C GROUP I OR ANNEX F SUBSTANCES')}</b><br><small>${$gettext('in metric tons (not ODP or CO₂-equivalent tonnes).')}</small>`,
        detailsHtml: $gettext('Fill in this form only if your country generated HFC-23 from any facility that produced (manufactured) Annex C Group I or Annex F substances.'),
        isInvalid: false,
        // used for identification when adding labels
        form_fields: [],
        get fields_order() {
          return this.section_subheaders.map(x => x.name)
        },
        section_subheaders: [{
          label: `(1) <br> ${$gettext('Facility name or identifier')}`,
          name: 'facility_name'
        },
        {
          label: `(2) <br> ${$gettext('Total amount generated')}`,
          name: 'quantity_generated'
        },
        {
          label: `(3a) <br> ${$gettext('For all uses')}`,
          name: 'quantity_captured_all_uses'
        },
        {
          label: `(3b) <br> ${$gettext('For feedstock use in your country')}`,
          name: 'quantity_captured_feedstock'
        },
        {
          label: `(3c) <br> ${$gettext('For destruction')}`,
          name: 'quantity_captured_for_destruction'
        },
        {
          label: `(4) <br> ${$gettext('Amount used for feedstock without prior capture')}`,
          name: 'quantity_feedstock'
        },
        {
          label: `(5) <br> ${$gettext('Amount destroyed without prior capture')}`,
          name: 'quantity_destroyed'
        },
        {
          label: `(6) <br> ${$gettext('Amount of generated emissions')}`,
          name: 'quantity_emitted'
        },
        {
          label: `(7a) <br> ${$gettext('Remarks (party)')}`,
          name: 'remarks_party'
        },
        {
          label: `(7b) ${$gettext('Remarks (secretariat)')}`,
          name: 'remarks_os'
        },
        {
          label: `${$gettext('Actions')}`,
          name: 'validation'
        }
        ],

        section_headers: [{
          label: ''
        },
        {
          label: ''
        },
        {
          label: '',
          tooltip: $gettext('Refers to the total amount whether captured or not. The sum of these amounts is not to be reported under data form 3')
        },
        {
          label: `(3) ${$gettext('Amount generated and captured')}`,
          tooltip: $gettext('Refers to the total amount whether captured or not. The sum of these amounts is not to be reported under data form 3'),
          colspan: 3
        },
        {
          label: '',
          tooltip: $gettext('Amount converted to other substances in the facility. The sum of these amounts is not to be reported under data form 3')
        },
        {
          label: '',
          tooltip: $gettext('Amount destroyed in the facility')
        },
        {
          label: ''
        },
        {
          label: ''
        },
        {
          label: ''
        },
        {
          label: ''
        }
        ],
        comments: {
          emissions_remarks_party: {
            selected: '',
            type: 'textarea'
          },
          emissions_remarks_secretariat: {
            selected: '',
            type: 'textarea'
          }
        },
        default_properties: {
          remarks_party: '',
          remarks_os: '',
          facility_name: '',
          quantity_generated: null,
          quantity_captured_all_uses: null,
          quantity_captured_feedstock: null,
          quantity_captured_for_destruction: null,
          quantity_feedstock: null,
          quantity_destroyed: null,
          quantity_emitted: null
        }
      },
      flags: getTabFlags($gettext)
    }
  }
  form.tabs.flags.showValid = true
  return form
}

export {
  getFormArt7
}
