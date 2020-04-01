<template>
  <div v-if="tabName">
    <div class="container">
      <h5 class="mt-2">
        <span v-translate>Add substances</span>
      </h5>
      <small>
        <span
          v-translate
        >Filter annex groups in order to select one or more substances. A row for each substance will be added in substances table. Substances can be deleted using table controls.</span>
      </small>
      <b-input-group id="substance_annex_selector" class="mt-2" :prepend="$gettext('Annex groups')">
        <multiselect
          :placeholder="$gettext('Select option')"
          @input="prepareSubstances"
          :multiple="true"
          label="text"
          :hide-selected="true"
          :close-on-select="true"
          trackBy="value"
          v-model="selected_groups.selected"
          :options="selected_groups.options"
        />
      </b-input-group>
      <b-input-group id="substance_selector" class="mb-2 mt-2" :prepend="$gettext('Substances')">
        <multiselect
          :placeholder="$gettext('Select option')"
          :hide-selected="true"
          :clear-on-select="true"
          :close-on-select="false"
          label="text"
          trackBy="value"
          :multiple="true"
          v-model="selected_substance.selected"
          @change="updateGroup($event)"
          :options="selected_substance.options"
        />
      </b-input-group>
      <b-btn-group>
        <b-btn
          id="add-substance-button"
          v-if="selected_substance.selected"
          :disabled="!selected_substance.selected.length"
          @click="addSubstance"
          variant="primary"
        >
          <span
            v-translate="selected_substance.selected.length ? {length: selected_substance.selected.length} : {length: ''}"
          >Add %{length} substances</span>
        </b-btn>
        <b-btn variant="light" v-if="selected_substance.selected && selected_substance.selected.length" @click="resetData">
          <span v-translate>Cancel</span>
        </b-btn>
      </b-btn-group>
    </div>
  </div>
</template>

<script>

import Multiselect from '@/components/common/ModifiedMultiselect'
import { getAlerts } from '@/components/common/dataDefinitions/alerts'

export default {

  props: {
    tabName: String
  },

  components: {
    Multiselect
  },

  computed: {
    substances() {
      // TODO: REMOVE FIRST FILTER IN 2033
      return this.tabName === 'has_nonparty' ? this.$store.state.initialData.substances.filter(s => s.group.group_id !== 'F' && s.group.group_id !== 'uncontrolled') : this.$store.state.initialData.substances.filter(s => s.group.group_id !== 'uncontrolled')
    },
    exemptions() {
      return this.$store.state.initialData.approvedExemptionsList
    }
  },

  mounted() {
    this.prepareGroups()
  },

  data() {
    return {
      alerts: getAlerts(this.$gettext),
      selected_substance: {
        selected: null,
        group: null,
        options: []
      },

      selected_groups: {
        selected: [],
        options: []
      },

      group_field: {
        label: '',
        name: '',
        substance: null
      }
    }
  },

  created() {
  },

  methods: {

    prepareSubstances() {
      this.selected_substance.options = []
      this.selected_substance.selected = []
      this.substances.forEach(substance => {
        if (this.selected_groups.selected.length) {
          if (this.selected_groups.selected.includes(substance.group.group_id)) {
            this.selected_substance.options.push({ text: substance.text, value: substance.value })
          }
        } else {
          this.selected_substance.options.push({ text: substance.text, value: substance.value })
        }
      })
    },

    pushUnique(array, item) {
      if (array.indexOf(item) === -1) {
        array.push(item)
      }
    },

    prepareGroups() {
      this.substances.forEach(substance => {
        if (!this.selected_groups.options.find(option => option && option.value === substance.group.group_id)) {
          this.selected_groups.options.push({ text: `${substance.group.name} ${substance.group.description}`, value: substance.group.group_id })
        }
      })
      this.prepareSubstances()
    },

    updateGroup(selected_substance) {
      this.substances.forEach(substance => {
        if (selected_substance.includes(substance.value)) {
          this.group_field.label = substance.group.group_id
          this.group_field.name = substance.group.group_id
        }
      })
    },

    addSubstance() {
      const ordered_selected_substance = this.selected_substance.options.filter(option => this.selected_substance.selected.includes(option.value)).map(s => s.value)
      this.updateGroup(ordered_selected_substance)

      for (const subst of ordered_selected_substance) {
        this.addSubstanceRaf(subst, { is_emergency: false })
      }
      this.resetData()
    },

    addSubstanceRaf(subst, prefillData) {
      console.log('adding', prefillData, subst)
      // substanceList, currentSectionName, groupName, currentSection, country, blend, prefillData
      this.$store.dispatch('createSubstance', {
        $gettext: this.$gettext,
        substanceList: [subst],
        currentSectionName: this.tabName,
        groupName: this.group_field.name,
        country: null,
        blendList: null,
        prefillData: prefillData || null,
        critical: this.$store.getters.getCriticalSubstances(subst)
      })
    },

    resetData() {
      this.selected_substance.selected = []
      this.selected_substance.options = []
      this.selected_groups.selected = []
      this.group_field = {
        label: '',
        name: '',
        substance: null
      }
      this.prepareSubstances()
    },

    removeSpecialChars(str) {
      return str.replace(/[^a-zA-Z0-9]+/g, '')
    }
  },

  watch: {
    substances: {
      handler() {
        this.prepareGroups()
      }
    }
  }

}
</script>
