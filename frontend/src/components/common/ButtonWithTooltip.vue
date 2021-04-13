<template>
  <b-btn
    v-if="hasTooltip"
    v-b-tooltip.hover.top="tooltip"
    :variant="variant"
    @click="$emit('click')"
  >
    <span>{{label}}</span>
  </b-btn>
  <b-btn
    v-else
    variant="outline-primary"
    @click="$emit('click')"
  >
    <span>{{label}}</span>
  </b-btn>
</template>

<script>

export default {
  props: {
    tooltip: String,
    label: String,
    variant: String,
    hasTooltip: Boolean
  },
  data() {
    return {}
  }
}
</script>
