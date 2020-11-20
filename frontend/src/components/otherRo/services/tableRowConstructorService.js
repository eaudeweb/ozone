import fromExponential from 'from-exponential/dist/index.min.js'
import { isNumber } from '@/components/common/services/utilsService'

const valueConverter = (item) => {
  if (item === null || item === undefined || Number.isNaN(parseFloat(item))) {
    return 0
  }
  return parseFloat(item)
}

// eslint-disable-next-line no-unused-vars
const doSum = (sumItems) => sumItems.reduce((sum, item) => valueConverter(item) + valueConverter(sum))

export default {
  nonSubstanceRows({
    currentSectionName, prefillData
  }) {
    let row
    switch (currentSectionName) {
    case 'procagent':
      row = {
        application_substance: {
          selected: null,
          type: 'nonInput'
        },
        application: {
          selected: null,
          type: 'nonInput'
        },
        decision: {
          selected: null,
          type: 'nonInput'
        },
        makeup_quantity: {
          selected: null,
          type: 'nonInput'
        },
        contain_technologies: {
          selected: null,
          type: 'nonInput'
        },
        emissions: {
          selected: null,
          type: 'nonInput'
        },
        units: {
          selected: null,
          type: 'nonInput'
        },
        remark: {
          selected: null,
          type: 'nonInput'
        },
        get validation() {
          return []
        }
      }
      if (prefillData) {
        Object.keys(prefillData).forEach((element) => {
          if (row[element]) {
            row[element].selected = isNumber(prefillData[element]) ? parseFloat(fromExponential(prefillData[element])) : prefillData[element]
          }
        })
      }
      return row
    default:
      break
    }
  },

  substanceRows({
    // eslint-disable-next-line no-unused-vars
    $gettext, section, substance, group, country, blend, prefillData
  }) {
    let baseInnerFields = {}
    switch (section) {
    case 'transfer':
      baseInnerFields = {
        transfer_type: {
          selected: null,
          type: 'nonInput'
        },
        source_party: {
          selected: null,
          type: 'nonInput'
        },
        destination_party: {
          selected: null,
          type: 'nonInput'
        },
        reporting_period: {
          selected: null,
          type: 'nonInput'
        },
        substance: {
          selected: substance,
          type: 'nonInput'
        },
        transferred_amount: {
          selected: null,
          type: 'nonInput'
        },
        is_basic_domestic_need: {
          selected: null,
          type: 'checkbox',
          disabled: true
        },
        get validation() {
          return []
        }
      }
      break
    default:
      break
    }
    if (prefillData) {
      Object.keys(prefillData).forEach((field) => {
        baseInnerFields[field]
          ?	baseInnerFields[field].selected = isNumber(prefillData[field])
            ? parseFloat(fromExponential(prefillData[field])) : prefillData[field]
          : null
      })
    }
    return baseInnerFields
  }

}
