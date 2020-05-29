<template>
  <div v-if="field && tabName">
    <b-btn class="mt-1" size="sm" variant="outline-dark" id="show-btn" @click="openModalAndSelect">Add countries</b-btn>
    <b-modal size="lg"  @shown="openCountryList" :id="`countries-modal-${this._uid}`" :ref="`countries-modal-${this._uid}`" :title="$gettext('Select one or more countries/regions/territories')">
        <b-row>
          <b-col cols="8">
            <div ref="countries_selector" style="position: relative; width: 100%;">
              <multiselect
                :max-height="250"
                :multiple="true"
                :clear-on-select="true"
                :hide-selected="false"
                :close-on-select="false"
                :disabled="disabled"
                label="text"
                trackBy="value"
                v-model="selected_countries.selected"
                :options="countryOptions"
              />
            </div>
          </b-col>
          <b-col>
            <b-btn
              @click="addSubstance"
              variant="primary"
              v-if="selected_countries.selected.length"
              >
              <span v-translate="{length: selected_countries.selected.length}">Add %{length} countries/regions/territories</span>
            </b-btn>
          </b-col>
        </b-row>

        <template slot="modal-footer">
          <b-btn variant="outline-danger" @click="resetData();$refs[`countries-modal-${_uid}`].hide()">Cancel</b-btn>
        </template>
      </b-modal>
  </div>
</template>
<script>

import Multiselect from '@/components/common/ModifiedMultiselect'
import { getAlerts } from '@/components/common/dataDefinitions/alerts'

export default {

  props: {
    tabName: String,
    current_field: Object,
    disabled: Boolean
  },

  components: {
    Multiselect
  },

  created() {
    this.field = JSON.parse(JSON.stringify(this.current_field))
  },

  computed: {
    countryOptions() {
      if (this.tabName === 'has_nonparty' && this.field.substance.selected) {
        return this.$store.state.initialData.nonParties && this.$store.state.initialData.countryOptions.filter(country => this.$store.state.initialData.nonParties[this.current_field.group.selected][country.value])
      }
      return this.$store.state.initialData.countryOptions
    }
  },

  data() {
    return {
      field: null,
      alerts: getAlerts(this.$gettext),
      selected_countries: {
        selected: []
      }
    }
  },

  methods: {
    openModalAndSelect() {
      this.$refs[`countries-modal-${this._uid}`].show()
    },

    openCountryList() {
      this.$refs.countries_selector.querySelector('.multiselect').focus()
    },
    addSubstance() {
      const current_field = JSON.parse(JSON.stringify(this.field))
      const current_fieldWithData = JSON.parse(JSON.stringify(this.current_field))
      const typeOfCountryFields = ['destination_party', 'source_party', 'trade_party']
      let currentTypeOfCountryField = ''
      const willNotAdd = []

      typeOfCountryFields.forEach(type => {
        if (current_field.hasOwnProperty(type)) currentTypeOfCountryField = type
      })

      let prefillData = null
      if (this.selected_countries.selected.length === 1) {
        prefillData = {}
        Object.keys(current_fieldWithData).forEach(key => {
          prefillData[key] = current_fieldWithData[key].selected
        })
        delete prefillData[currentTypeOfCountryField]
        delete prefillData.validation
      }

      this.selected_countries.selected.forEach(country => {
        let fieldExists = false
        for (const existing_field of this.$store.state.form.tabs[this.tabName].form_fields) {
          if (current_field.substance.selected) {
            if (parseInt(existing_field.substance.selected) === parseInt(current_field.substance.selected) && parseInt(existing_field[currentTypeOfCountryField].selected) === parseInt(country)) {
              fieldExists = true
              willNotAdd.push(country)
              break
            }
          } else if (current_field.blend.selected) {
            if (parseInt(existing_field.blend.selected) === parseInt(current_field.blend.selected) && parseInt(existing_field[currentTypeOfCountryField].selected) === parseInt(country)) {
              fieldExists = true
              willNotAdd.push(country)
              break
            }
          }
        }
        // substanceList, currentSectionName, groupName, currentSection, country, blend, prefillData
        if (!fieldExists) {
          this.$store.dispatch('createSubstance', {
            $gettext: this.$gettext,
            substanceList: [current_field.substance.selected],
            currentSectionName: this.tabName,
            groupName: current_field.group.selected,
            country,
            blendList: [current_field.blend.selected],
            prefillData
          })
        }
      })
      const willNotAddCountryNames = []
      willNotAdd.length && willNotAdd.forEach(countryId => {
        const { text } = this.countryOptions.find(countryDisplay => countryDisplay.value === countryId)
        if (text) {
          willNotAddCountryNames.push(text)
        }
      })
      willNotAddCountryNames.length && this.$store.dispatch('setAlert', {
        $gettext: this.$gettext,
        message: { __all__: [`${this.alerts.field_already_exists} : ${willNotAddCountryNames.join(', ')}`] },
        variant: 'danger'
      })
      this.$refs[`countries-modal-${this._uid}`].hide()
      this.$emit('removeThisField')
      this.resetData()
      this.cleanupModalMess()
    },

    resetData() {
      this.selected_countries.selected = []
    },
    cleanupModalMess() {
      const body = document.querySelector('body')
      body.classList.remove('modal-open')
      body.setAttribute('style', '')
      body.setAttribute('data-modal-open-count', '0')
    },
    removeSpecialChars(str) {
      return str.replace(/[^a-zA-Z0-9]+/g, '')
    }
  },
  watch: {
    current_field: {
      handler() {
        this.field = JSON.parse(JSON.stringify(this.current_field))
      }
    }
  }
}
</script>
