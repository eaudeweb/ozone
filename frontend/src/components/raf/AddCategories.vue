<template>
  <div v-if="tabName">
    <b-row>
      <b-col lg="9">
        <b-input-group
          id="categories_selector"
          class="mb-2 mt-2"
          :prepend="$gettext('Add categories')"
        >
          <multiselect
            :placeholder="$gettext('Select option')"
            :clear-on-select="false"
            :hide-selected="false"
            :close-on-select="false"
            label="text"
            trackBy="value"
            :multiple="true"
            v-model="selected_categories.selected"
            :disabled="!$store.getters.edit_mode"
            :options="categories"
          />
        </b-input-group>
      </b-col>
      <b-col class="flex-center">
        <b-btn-group>
          <b-btn
            :disabled="!selected_categories.selected.length"
            @click="addEntries"
            variant="primary"
          >
            <span
              v-html="$store.getters.edit_mode ?
                `Add ${selected_categories.selected.length > 0 ? selected_categories.selected.length : ''} categories`
                : `Enable edit mode`"
            ></span>
          </b-btn>
          <b-btn v-if="selected_categories.selected.length" @click="resetData">
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
    index: Number
  },

  components: {
    Multiselect
  },

  computed: {
    categories() {
      return this.$store.state.initialData.criticalUseCategoryList
    }
  },

  mounted() {
  },

  data() {
    return {
      selected_categories: {
        selected: []
      }
    }
  },

  created() {
  },

  methods: {
    resetData() {
      this.selected_categories.selected = []
    },
    addEntries() {
      this.$store.commit('addCategoryEntry', { tabName: this.tabName, index: this.index, categoryList: this.selected_categories.selected })
      this.resetData()
    }
  }
}
</script>
