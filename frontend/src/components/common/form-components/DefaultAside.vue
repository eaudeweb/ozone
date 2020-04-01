<template>
  <div>
    <AsideToggler :validationButton="showValidationButton" :hasAssideMenu="$store.state.form.tabs[tabName].hasAssideMenu" />
    <b-tabs no-key-nav v-model="tabIndex">
      <b-tab v-if="hasSubstances && canEditSubstanceData">
        <template slot="title">
          <span v-translate>Substances</span>
        </template>
        <add :tabName="tabName"></add>
      </b-tab>
      <b-tab v-if="hasBlends && canEditSubstanceData">
        <template slot="title">
          <span v-translate>Mixtures</span>
        </template>
        <AddBlend :tabName="tabName"></AddBlend>
      </b-tab>
      <b-tab :title-link-class="validationLength > 0 ? {} : null">
        <template slot="title">
          <span v-translate>Validation</span>
          <b-badge :style="{marginLeft: '5px'}" v-if="validationLength" variant="danger">{{validationLength}}</b-badge>
        </template>
        <Validation
          v-on:fillSearch="$emit('fillSearch', $event)"
          :hovered="hovered"
          :tabName="tabName"
        ></Validation>
      </b-tab>
    </b-tabs>
    <div class="legend">
      <b>
        <span v-translate>Legend</span>
      </b>
      <hr>
      <div>
        <div class="spinner">
          <div class="loader"></div>
        </div> &nbsp;
        <span v-translate>Operation in progress</span>
      </div>
      <div>
        <i style="color: red;" class="fa fa-exclamation-circle fa-lg"></i> &nbsp;
        <span v-translate>Validation errors</span>
      </div>
      <div>
        <i style="color: green;" class="fa fa-check-circle fa-lg"></i> &nbsp;
        <span
          v-translate
        >Data is valid and saved</span>
      </div>
      <div>
        <i class="fa fa-edit fa-lg"></i> &nbsp;
        <span
          v-translate
        >Submission edited. Please save before closing the form </span>
      </div>
    </div>
  </div>
</template>

<script>

import AsideToggler from './AsideTogglerModified'
import Add from './Add'
import AddBlend from './AddBlend'
import Validation from './Validation'

export default {
  name: 'DefaultAside',

  components: {
    add: Add,
    AddBlend,
    AsideToggler,
    Validation
  },

  props: {
    hovered: null,
    tabName: String,
    parentTabIndex: Number,
    canEditSubstanceData: Boolean
  },

  data() {
    return {
      tabIndex: 0
    }
  },

  computed: {
    hasSubstances() {
      return Object.keys(this.$store.state.form.tabs[this.tabName].default_properties).includes('substance')
    },
    hasBlends() {
      return Object.keys(this.$store.state.form.tabs[this.tabName].default_properties).includes('blend')
    },
    showValidationButton() {
      return !this.canEditSubstanceData && this.validationLength > 0
    },
    validationLength() {
      return this.$store.getters.getValidationForCurrentTab(this.tabName).filter(field => field.validation.length).length
    }
  },

  watch: {
    parentTabIndex: {
      handler(new_val) {
        if (new_val !== this.tabIndex) {
          console.log(new_val)
          this.tabIndex = new_val
        }
      }
    },
    tabIndex: {
      handler(new_val) {
        if (new_val !== this.parentTabIndex) {
          this.$emit('update:parentTabIndex', new_val)
        }
      }
    }
  }

}
</script>
<style scoped>
.legend {
  padding: .2rem 2rem;
  background: white;
  margin-bottom: 3.5rem;
}

.legend .loader {
	animation: unset;
}

.legend .spinner {
  margin-left: 0;
}
</style>
