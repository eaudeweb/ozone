<template>
  <div>
    <tabsmanager v-if="initialDataReady" :submission="submission" />
  </div>
</template>

<script>
import tabsManager from '@/components/otherRo/TabsManager'
import dataManagerMixin from '@/components/common/mixins/DataManagerMixin'

export default {
  name: 'DataManager',
  components: {
    tabsmanager: tabsManager
  },
  mixins: [dataManagerMixin]
}
</script>
