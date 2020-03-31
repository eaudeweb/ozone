<template>
  <multiselect
    v-bind="$attrs"
    v-on="forwardListeners"
    v-model="completeValue"
    :options="options"
    :track-by="trackBy"
    :label="label"
    :disabled="disabled"
  >
    <template v-if="customTemplate" slot="singleLabel" slot-scope="props">
      <div :class="{highlighted: props.option[customTemplate]}">
        <span v-html="props.option[customTemplate] ? `${customTemplateText} ` : ''"></span>
        <span class="option__title">{{ props.option[label] }}</span>
      </div>
    </template>

    <template v-if="customTemplate" slot="option" slot-scope="props">
      <div :class="{highlighted: props.option[customTemplate]}">
        <span v-html="props.option[customTemplate] ? `${customTemplateText} ` : ''"></span>
        <span class="option__title">{{ props.option[label] }}</span>
      </div>
    </template>
  </multiselect>
</template>
<script>
import Multiselect from 'vue-multiselect'

export default {
  inheritAttrs: false,
  components: {
    Multiselect
  },
  props: ['value', 'options', 'trackBy', 'customTemplate', 'customTemplateText', 'label', 'disabled'],
  computed: {
    completeValue: {
      get() {
        return this.$attrs.multiple
          ? this.value ? this.value.map(value => this.findOption(value)) : null
          : this.findOption(this.value)
      },
      set(v) {
        this.$emit('input', this.$attrs.multiple
          ? v.map(value => value[this.trackBy])
          : (v && v[this.trackBy]))
      }
    },
    forwardListeners() {
      const { input, ...listeners } = this.$listeners
      return listeners
    }
  },
  methods: {
    findOption(value) {
      return this.options.find(option => option[this.trackBy] === value)
    }
  }
}
</script>

<style type="text/css">
.highlighted {
  color: #e6b222;
  font-weight: bold;
}
</style>
