<template>
  <div v-if="tabName && parties">
    <b-row>
      <b-col lg="9">
        <b-input-group
          id="countries_selector"
          class="mb-2 mt-2"
          :prepend="$gettext('Add countries')"
        >
          <multiselect
            :placeholder="$gettext('Select option')"
            :clear-on-select="true"
            :hide-selected="true"
            :close-on-select="false"
            label="text"
            trackBy="value"
            :multiple="true"
            v-model="selected_countries.selected"
            :options="countries"
          />
        </b-input-group>
      </b-col>
      <b-col class="flex-center">
        <b-btn-group>
          <b-btn
            :disabled="!selected_countries.selected.length"
            @click="addEntries"
            variant="primary"
          >
            <span
              v-translate="selected_countries.selected.length ? {length: selected_countries.selected.length} : {length: ''}"
            >Add %{length} countries</span>
          </b-btn>
          <b-btn v-if="selected_countries.selected.length" @click="resetData">
            <span v-translate>Cancel</span>
          </b-btn>
        </b-btn-group>
      </b-col>
    </b-row>
  </div>
</template>

<script>

import Multiselect from '@/components/common/ModifiedMultiselect'

export default {

  props: {
    tabName: String,
    index: Number,
    parties: Array
  },

  components: {
    Multiselect
  },

  computed: {
    countries() {
      return this.$store.state.initialData.countryOptions.filter(o => !this.parties.find(p => parseInt(p.party) === parseInt(o.value)))
    }
  },

  mounted() {
  },

  data() {
    return {
      selected_countries: {
        selected: []
      }
    }
  },

  created() {
  },

  methods: {
    resetData() {
      this.selected_countries.selected = []
    },
    addEntries() {
      this.$store.commit('addCountryEntries', { tabName: this.tabName, index: this.index, countryList: this.selected_countries.selected })
      this.resetData()
    }
  }
}
</script>
