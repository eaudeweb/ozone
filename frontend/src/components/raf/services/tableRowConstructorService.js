import fromExponential from 'from-exponential/dist/index.min.js'
import { isNumber, doSum } from '@/components/common/services/utilsService'

const valueConverter = (item) => {
  if (item === null || item === undefined || Number.isNaN(parseFloat(item))) {
    return 0
  }
  return parseFloat(item)
}
const createTooltip = (fields, section, $gettext, countries) => {
  let tooltip_title = ''
  if (Object.keys(fields).length) {
    Object.keys(fields).forEach(field => {
      tooltip_title += `${countries[field] || $gettext('Unspecified')} : ${fromExponential(fields[field])}\n`
    })
  }
  tooltip_title += `\n ${$gettext('Click to edit')}`
  return tooltip_title
}

const quantityCalculator = (fields, parent, section, $gettext, countries) => {
  let count = 0
  const returnObj = {
    tooltip: '',
    type: 'nonInput',
    selected: count
  }

  const forTooltip = {}
  fields.forEach(field => {
    count = doSum([count, field.quantity])
    forTooltip[field.party ? field.party : field.critical_use_category] = valueConverter(field.quantity)
  })

  if (count === 0) {
    returnObj.selected = null
  } else {
    returnObj.selected = fromExponential(count)
  }

  const tooltip = createTooltip(forTooltip, section, $gettext, countries)
  returnObj.tooltip = tooltip

  return returnObj
}

// eslint-disable-next-line no-unused-vars

export default {
  substanceRows({
    // eslint-disable-next-line no-unused-vars
    $gettext, section, substance, group, country, blend, prefillData, countries, critical, exemptionValue, critical_use_categories, has_critical_uses
  }) {
    const	baseInnerFields = {
      checkForDelete: {
        selected: false,
        type: 'checkbox'
      },
      remarks_party: {
        type: 'textarea',
        selected: ''
      },
      remarks_os: {
        type: 'textarea',
        selected: ''
      },
      group: {
        selected: group,
        type: 'nonInput'
      },
      substance: {
        type: 'select',
        selected: substance || null
      },
      quantity_exempted: {
        type: 'nonInput',
        selected: null,
        exemptionValue
      },
      quantity_production: {
        type: 'number',
        selected: null
      },
      imports: [
        {
          party: 9999,
          quantity: 0
        }
      ],
      get quantity_import() {
        return quantityCalculator(this.imports, this, section, $gettext, countries)
      },
      get quantity_acquired() {
        return {
          type: 'nonInput',
          selected: doSum([this.quantity_production.selected, this.quantity_import.selected])
        }
      },
      get quantity_authorized_not_acquired() {
        return {
          type: 'nonInput',
          selected: doSum([this.quantity_exempted.selected, -this.quantity_acquired.selected])
        }
      },
      on_hand_start_year: {
        type: 'number',
        selected: null
      },
      get available_for_use() {
        return {
          type: 'nonInput',
          selected: doSum([this.on_hand_start_year.selected, this.quantity_acquired.selected])
        }
      },
      is_emergency: {
        type: 'checkbox',
        selected: false
      },
      quantity_used: {
        type: 'number',
        selected: null
      },
      set quantity_use_categories(val) {
        const self = this
        if (!this.use_categories.length && has_critical_uses) {
          this.use_categories = [{
            code: 'OTHER',
            critical_use_category: Object.keys(critical_use_categories).find(c => ['Other', 'Unspecified'].includes(critical_use_categories[c])),
            quantity: self.quantity_used.selected || 0
          }]
          this.quantity_used = quantityCalculator(this.use_categories, this, section, $gettext, critical_use_categories)
        }
        if (has_critical_uses) {
          this.quantity_used = quantityCalculator(this.use_categories, this, section, $gettext, critical_use_categories)
        }
      },
      use_categories: [],
      quantity_exported: {
        type: 'number',
        selected: null
      },
      quantity_destroyed: {
        type: 'number',
        selected: null
      },
      get on_hand_end_year() {
        const criticalValue = critical ? valueConverter(this.quantity_exported.selected) : 0
        return {
          type: 'nonInput',
          selected: doSum([this.available_for_use.selected, -this.quantity_used.selected, -criticalValue, -this.quantity_destroyed.selected])
        }
      },
      get validation() {
        const errors = []
        if (this.on_hand_end_year.selected === null) {
          errors.push($gettext('Please fill-in column On hand end of year (13)'))
        }
        // TODO: WIP
        // if (valueConverter(this.quantity_import.selected) > valueConverter(this.quantity_acquired.selected)) {
        //   errors.push($gettext('Sum of amounts by country should not be higher than the total amount imported'))
        // }

        const returnObj = {
          type: 'nonInput',
          selected: errors
        }

        return returnObj
      }
    }
    if (critical) {
      baseInnerFields.use_categories = [{
        code: 'OTHER',
        critical_use_category: Object.keys(critical_use_categories).find(c => ['Other', 'Unspecified'].includes(critical_use_categories[c])),
        quantity: 0
      }]
    }

    if (prefillData) {
      console.log('prefillData', prefillData)
      Object.keys(prefillData).forEach((field) => {
        if (Array.isArray(prefillData[field]) && field === 'imports') {
          baseInnerFields[field] = prefillData[field]
        }
        if (Array.isArray(prefillData[field]) && field === 'use_categories') {
          baseInnerFields[field] = prefillData[field]
        }
        console.log(field)
        baseInnerFields[field]
          ?	baseInnerFields[field].selected = isNumber(prefillData[field])
            ? parseFloat(fromExponential(prefillData[field])) : prefillData[field]
          : null
      })
    }
    baseInnerFields.quantity_use_categories = null

    return baseInnerFields
  }

}
