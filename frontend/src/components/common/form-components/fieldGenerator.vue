<template>
  <div v-if="field" class="position-relative">
    <div
      v-if="field.type === 'text' || field.type === 'number' || field.type ==='email' || field.type === 'nonInput'"
    >
      <span
        class="nonInput"
        v-if="field.type === 'nonInput'"
        :id="fieldInfo ? fieldInfo.field : ''"
      >{{field.selected}}</span>
      <input
        v-else
        :id="fieldInfo ? fieldInfo.field : ''"
        @keyup="validateInput"
        @change="updateFormField"
        autocomplete="off"
        :disabled="disabled"
        class="form-control"
        :actual_type="field.type"
        v-model="currentTyping"
        :type="field.type ==='number' ? 'text' : field.type"
      >
    </div>
    <Datepicker
      input-class="form-control"
      :disabled="disabled"
      :clear-button="!disabled"
      @input="updateFormField"
      v-model="currentTyping"
      :highlighted="{dates:[new Date()]}"
      :disabled-dates="disabledDates"
      :typeable=true
      format="d MMMM yyyy"
      v-else-if="field.type === 'date'"
    ></Datepicker>
    <b-form-radio-group
      :stacked="field.radioType"
      :id="field.name"
      @change="updateFormFieldWithTabs"
      :disabled="disabled"
      v-else-if="field.type === 'radio'"
      :checked="field.selected"
      :options="field.options"
    ></b-form-radio-group>

    <b-form-group :id="field.name" v-else-if="field.type === 'questionnaireRadio'">
        <b-form-checkbox
          v-for="(option, index) in field.options"
          :key="`${field.name}_${option.value}_${index}`"
          :id="`${field.name}_${option.value}_${index}`"
          :name="`${field.name}_${option.value}_${index}`"
          :value="option.value"
          :unchecked-value="null"
          :disabled="disabled"
          @change="updateFormFieldQuestionnaire($event, field.selected)"
          :checked="field.selected"
          inline
        >
        {{option.text}}
      </b-form-checkbox>
    </b-form-group>

    <b-form-checkbox
      :id="id"
      @change="updateFormFieldWithTabs"
      :disabled="field.disabled || disabled"
      v-else-if="field.type === 'checkbox'"
      v-model="currentTyping"
    ></b-form-checkbox>
    <div v-else-if="field.type === 'select'">
      <multiselect
        :placeholder="$gettext('Select option')"
        :multiple="false"
        label="text"
        :hide-selected="false"
        trackBy="value"
        @input="updateFormField($event)"
        :disabled="disabled"
        v-model="currentTyping"
        :options="fieldOptions"
      />
    </div>
    <textarea
      :id="fieldInfo ? fieldInfo.field : ''"
      @change="updateFormField"
      :disabled="disabled"
      class="form-control"
      v-else-if="field.type === 'textarea'"
      v-model="currentTyping"
    ></textarea>

    <ul v-else-if="field.type === 'list'">
      <li v-for="(item, id) in field.selected" :key="id">{{item}}</li>
    </ul>

    <input
      v-if="isMultipleField"
      :id="fieldInfo ? fieldInfo.field : ''"
      @keyup="validateInput"
      :disabled="disabled"
      autocomplete="off"
      @change="updateFormFieldMultiple"
      actual_type="number"
      class="form-control"
      v-model="currentTyping"
      type="text"
    >
    <i v-if="icon" :class="[icon.fa, 'field-icon']" v-b-tooltip:hover="icon.tooltip" @click="$emit('icon-clicked')"></i>
  </div>
</template>

<script>
import Datepicker from 'vuejs-datepicker'
import Multiselect from '@/components/common/ModifiedMultiselect'
import { fromExponential } from '@/components/common/services/utilsService'

export default {

  props: {
    field: Object,
    disabled: { type: Boolean, default: () => false },
    fieldInfo: Object,
    id: String,
    icon: Object
  },
  components: {
    Multiselect,
    Datepicker
  },
  created() {
    this.currentTyping = this.field.selected && this.field.type === 'number' ? fromExponential(this.field.selected) : this.field.selected
    if (this.isMultipleField) {
      this.currentTyping = this.field.quantity
    }
    if (this.field.type === 'select') {
      // Some numbers can arrive here (usually after prefill) as strings.
      // This issue affects only the select because of the pair (text - value) that needs to match
      this.currentTyping = Number(this.field.selected) || this.field.selected
    }
    if (this.$store.state.currentUser.is_secretariat) {
      this.disabledDates.from = new Date()
    }
  },

  data() {
    return {
      currentTyping: null,
      disabledDates: {}
    }
  },

  computed: {
    fieldOptions() {
      return this.field.options
    },
    isMultipleField() {
      return (this.field.hasOwnProperty('party') && this.field.hasOwnProperty('quantity')) || (this.field.hasOwnProperty('critical_use_category') && this.field.hasOwnProperty('quantity'))
    }
  },

  methods: {
    validateInput() {
      if (this.field.type === 'number') {
        const valid = /^-?\d+\.\d*$|^-?[\d]*$/
        const number = /-\d+\.\d*|-[\d]*|[\d]+\.[\d]*|[\d]+/
        if (this.currentTyping && !valid.test(this.currentTyping)) {
          const n = this.currentTyping.match(number)
          this.currentTyping = n ? parseFloat(n[0]) : null
        }
      }
    },

    updateFormField(e) {
      if (this.field.type !== 'select') {
        this.validateInput()
        // empty strings in number field are not accepted in backend, so we need to transform every '' into a null for type === number
        if (this.currentTyping === '' && this.field.type === 'number') {
          this.$store.commit('updateFormField', { value: null, fieldInfo: this.fieldInfo })
          return
        }
        if (this.field.type === 'number' && this.currentTyping !== '') {
          this.$store.commit('updateFormField', { value: parseFloat(this.currentTyping), fieldInfo: this.fieldInfo })
          return
        }
        this.$store.commit('updateFormField', { value: this.currentTyping, fieldInfo: this.fieldInfo })
      } else {
        this.$store.commit('updateFormField', { value: e, fieldInfo: this.fieldInfo })
      }
    },

    updateFormFieldMultiple() {
      this.validateInput()
      if (this.currentTyping === '') {
        this.$store.commit('updateFormField', { value: null, fieldInfo: this.fieldInfo })
      } else {
        this.$store.commit('updateFormField', { value: parseFloat(this.currentTyping), fieldInfo: this.fieldInfo })
      }
    },

    updateFormFieldWithTabs(event) {
      this.$emit('change', this.fieldInfo)
      this.$store.commit('updateFormField', { value: event, fieldInfo: this.fieldInfo })
    },
    updateFormFieldQuestionnaire(event) {
      this.$store.commit('updateFormField', { value: event, fieldInfo: this.fieldInfo })
    }
  },
  watch: {
    'field.selected': {
      handler() {
        this.currentTyping = this.field.selected && this.field.type === 'number' ? fromExponential(this.field.selected) : this.field.selected
      }
    }
  }
}
</script>

<style lang="scss" scoped>
  .field-icon {
    position: absolute;
    top: 50%;
    left: 5px;
    transform: translateY(-50%);
    cursor: pointer;
  }
</style>
