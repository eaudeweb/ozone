<template>
  <div>
    <div class="container">
      <div v-if="!new_blend">
        <h5 class="mt-2">
          <span v-translate>Add predefined mixtures</span>
        </h5>
        <small>
          <span
            v-translate
          >Filter by mixture types in order to select one or more mixtures. A row for each mixture will be added in mixtures table. Mixtures can be deleted using table controls.</span>
        </small>
        <b-input-group id="blend_type_selector" class="mt-2" prepend="Mixture types">
          <multiselect
            :placeholder="$gettext('Select option')"
            :clear-on-select="false"
            :hide-selected="true"
            trackBy="value"
            label="text"
            :close-on-select="true"
            :multiple="true"
            @input="new_blend = null; selected_blends.selected = []"
            v-model="selected_blends.filter"
            :options="selected_blends.filters"
          />
        </b-input-group>

        <div class="mt-2 mb-2" style="display: flex;">
          <b-input-group id="blend_selector" class="mt-2" prepend="Mixtures">
            <multiselect
              :placeholder="$gettext('Select option')"
              trackBy="value"
              :hide-selected="true"
              :clear-on-select="true"
              :close-on-select="false"
              :multiple="true"
              label="text"
              v-model="selected_blends.selected"
              @input="new_blend = null"
              :options="filteredBlends"
            />
          </b-input-group>
        </div>
      </div>

      <div v-if="selected_blends.selected">
        <div
          :key="blend.name"
          v-for="blend in selected_blends.selected"
          class="small mb-2"
        >
          <div>
            <span class="mr-1" v-translate>Composition of</span>
            <b>{{display.blends[blend].name}}</b>
          </div>
          <b-row
            v-for="(substance, substance_index) in display.blends[blend].components"
            :key="substance_index"
          >
            <b-col>{{substance.component_name}}</b-col>
            <b-col>{{substance.percentage.toLocaleString("en", {style: "percent"})}}</b-col>
          </b-row>
        </div>
      </div>
      <b-btn-group>
        <b-btn
          v-if="selected_blends.selected.length"
          @click="addSubstance('selected')"
          id="add-blend-button"
          variant="primary"
        >
          <span v-translate="{length: selected_blends.selected.length}">Add %{length} mixtures</span>
        </b-btn>
        <b-btn variant="light" v-if="selected_blends.selected.length" @click="resetData">Cancel</b-btn>
      </b-btn-group>

      <div v-if="!new_blend && !selected_blends.selected.length">
        <hr>
        <h5>
          <span v-translate>Add custom mixture</span>
        </h5>
        <b-btn variant="primary" @click="addNewBlend">
          <span v-translate>Add new mixture</span>
        </b-btn>
      </div>

      <div v-if="new_blend">
        <h5>
          <span v-translate>Add custom mixture</span>
        </h5>
        <small>
          <span
            v-translate
          >If a non-standard mixture not listed above please indicate the mixture name and the percentage by weight of each constituent controlled substance of the mixture. Please pay attention to the percentage values before adding a new mixture. For mistakes please contact secretariat to delete the mixture.</span>
        </small>
        <b-input-group class="mt-2" prepend="Mixture name">
          <b-form-input type="text" @blur.native="alertIfBlendExists" v-model="new_blend.text"></b-form-input>
          <b-input-group-append>
            <b-btn @click="addSubstanceToBlend">
              <span v-translate>Add substance</span>
            </b-btn>
          </b-input-group-append>
        </b-input-group>
        <b-input-group
          class="mb-2 mt-2"
          v-for="(substance, substance_index) in new_blend.composition"
          :key="substance_index"
        >
          <b-input-group-prepend>
            <b-btn
              style="z-index:initial;"
              variant="danger"
              @click="removeSubstanceFromBlend(substance)"
            >X</b-btn>
          </b-input-group-prepend>
          <multiselect
            label="text"
            @tag="addTag($event,substance)"
            :taggable="true"
            trackBy="value"
            :hide-selected="true"
            :close-on-select="true"
            :tag-placeholder="$gettext('Press enter to use a new substance')"
            :placeholder="$gettext('Controlled or new substance')"
            v-model="substance.name"
            :options="substances"
            />
          <b-input-group-append>
            <b-input-group append="%">
              <b-form-input class="ml-2" type="text" placeholder v-model="substance.percent"></b-form-input>
            </b-input-group>
          </b-input-group-append>
        </b-input-group>
      </div>

      <hr>
      <b-btn-group>
        <b-btn
          v-if="new_blend"
          :disabled="!blendIsValid"
          @click="addSubstance('custom')"
          variant="primary"
        >
          <span v-translate>Add row</span>
        </b-btn>
        <b-btn variant="light" v-if="new_blend" @click="resetData">
          <span v-translate>Cancel</span>
        </b-btn>
      </b-btn-group>
    </div>
  </div>
</template>

<script>

import { createBlend } from '@/components/common/services/api'
import Multiselect from '@/components/common/ModifiedMultiselect'
import { getAlerts } from '@/components/common/dataDefinitions/alerts'

export default {

  props: {
    tabName: String
  },

  computed: {
    substances() {
      return JSON.parse(JSON.stringify(this.$store.state.initialData.substances))
    },

    blends() {
      return this.$store.state.initialData.blends
    },

    display() {
      return this.$store.state.initialData.display
    },

    blendIsValid() {
      return !this.$store.getters.checkIfBlendAlreadyEists(this.new_blend.text) && this.new_blend.composition.every((substance) => substance.name && substance.percent)
    },

    filteredBlends() {
      return this.selected_blends.filter.length
        ? this.selected_blends.options.filter(blend => this.selected_blends.filter.includes(blend.type)) : this.selected_blends.options
    }
  },

  components: {
    Multiselect
  },

  mounted() {
    this.prepareBlends()
  },

  data() {
    return {
      alerts: getAlerts(this.$gettext),
      new_blend: null,
      submit_blend: {
        components: null,
        blend_id: null,
        type: 'Custom'
      },
      selected_substance: {
        selected: null,
        group: null,
        options: []
      },
      selected_blends: {
        selected: [],
        options: [],
        filters: [],
        filter: [],
        substance_options: []
      }
    }
  },

  methods: {
    pushUnique(array, item) {
      if (array.indexOf(item) === -1) {
        array.push(item)
      }
    },

    addTag(newTag, substance) {
      console.log(newTag, substance)
      const tag = {
        text: newTag,
        value: newTag
      }
      this.substances.push(tag)
      substance.name = newTag
    },

    prepareSubstances() {
      this.selected_substance.options = this.substances.map(substance => ({
        value: substance.id,
        text: substance.name,
        group: substance.group
      }))
    },

    alertIfBlendExists() {
      console.log('here')
      if (this.$store.getters.checkIfBlendAlreadyEists(this.new_blend.text)) {
        this.$store.dispatch('setAlert', {
          $gettext: this.$gettext,
          message: { __all__: [`${this.alets.blend_already_exists} - ${this.new_blend.text}`] },
          variant: 'danger'
        })
      }
    },

    addNewBlend() {
      this.selected_blends.selected = []
      this.new_blend = {
        text: null,
        value: null,
        composition: [
          {
            name: null,
            percent: null
          },
          {
            name: null,
            percent: null
          },
          {
            name: null,
            percent: null
          }
        ]
      }
    },

    removeSubstanceFromBlend(substance) {
      this.new_blend.composition.splice(this.new_blend.composition.indexOf(substance), 1)
    },

    addSubstanceToBlend() {
      this.new_blend.composition.push({ name: null, percent: null })
    },

    prepareBlends() {
      this.selected_blends.filters = []
      this.selected_blends.options = []
      if (Array.isArray(this.blends) && this.blends.length > 0) {
        this.blends.forEach(blend => {
          this.selected_blends.options.push({ text: blend.blend_id, value: blend.id, type: blend.type, sort_order: blend.sort_order })
          this.pushUnique(this.selected_blends.filters, blend.type)
        })
      }
      this.selected_blends.filters = this.selected_blends.filters.map(b => ({ text: b, value: b }))
      this.selected_blends.options.sort((a, b) => a.sort_order - b.sort_order)
      this.prepareSubstances()
    },

    addSubstance(type) {
      if (type === 'selected') {
        const ordered_selected_blends = this.selected_blends.options.filter(option => this.selected_blends.selected.includes(option.value)).map(s => s.value)
        const current_field = this.$store.state.form.tabs[this.tabName].default_properties
        const typeOfCountryFields = ['destination_party', 'source_party', 'trade_party']
        let currentTypeOfCountryField = ''
        const willNotAdd = []

        typeOfCountryFields.forEach(typec => {
          if (current_field.hasOwnProperty(typec)) currentTypeOfCountryField = typec
        })

        for (const blend of ordered_selected_blends) {
          let fieldExists = false
          for (const existing_field of this.$store.state.form.tabs[this.tabName].form_fields) {
            if (parseInt(existing_field.blend.selected) === blend && existing_field[currentTypeOfCountryField].selected === null) {
              fieldExists = true
              willNotAdd.push(blend)
              break
            }
          }
          // substanceList, currentSectionName, groupName, currentSection, country, blend, prefillData
          if (!fieldExists) {
            this.$store.dispatch('createSubstance', {
              $gettext: this.$gettext,
              substanceList: null,
              currentSectionName: this.tabName,
              groupName: null,
              country: null,
              blendList: [blend],
              prefillData: null
            })
            this.resetData()
          }
        }

        const willNotAddSubstanceNames = []
        willNotAdd.length && willNotAdd.forEach(id => {
          const { blend_id } = this.blends.find(blendDisplay => blendDisplay.id === id)
          if (blend_id) {
            willNotAddSubstanceNames.push(blend_id)
          }
        })
        willNotAddSubstanceNames.length && this.$store.dispatch('setAlert', {
          $gettext: this.$gettext,
          message: { __all__: [`${this.alerts.blend_not_added} : ${willNotAddSubstanceNames.join(', ')}, <br> ${this.alerts.select_country_before_adding_again_blend}`] },
          variant: 'danger'
        })
        this.resetData()
      } else {
        this.submit_blend.blend_id = this.new_blend.text
        this.submit_blend.components = []
        this.submit_blend.party = this.$store.state.current_submission.party
        this.new_blend.composition.forEach(substance => {
          if (typeof (substance.name) === 'string') {
            this.submit_blend.components.push({ component_name: substance.name, substance: null, percentage: substance.percent / 100 })
          } else {
            this.submit_blend.components.push({ component_name: '', substance: substance.name, percentage: substance.percent / 100 })
          }
        })
        createBlend(this.submit_blend).then(response => {
          this.new_blend.value = response.data.id
          this.$store.commit('addCreateBlendToBlendList', response.data)
          this.display.blends[response.data.id] = { name: response.data.blend_id, components: response.data.components }
          this.$store.dispatch('createSubstance', {
            $gettext: this.$gettext,
            substanceList: null,
            currentSectionName: this.tabName,
            groupName: null,
            country: null,
            blendList: [this.new_blend.value],
            prefillData: null
          })
          this.$store.dispatch('setAlert', {
            $gettext: this.$gettext,
            message: { __all__: [this.alerts.blend_created] },
            variant: 'success' })
          this.resetData()
        }).catch((error) => {
          console.log(error)
          this.$store.dispatch('setAlert', {
            $gettext: this.$gettext,
            message: { ...error.response.data },
            variant: 'danger' })
        })
      }
    },

    resetData() {
      this.new_blend = null
      this.selected_blends.filter = []
      this.selected_blends.selected = []
      this.selected_blends.options = []
      this.prepareBlends()
    }

  },

  watch: {
    blends: {
      handler() {
        this.prepareBlends()
      }
    }
  }

}
</script>

<style lang="css" scoped>

.add-blend-wrapper {
	white-space: nowrap;
	margin-left: .5rem;
	display: flex;
	justify-content: center;
	align-items: center;
}
</style>
