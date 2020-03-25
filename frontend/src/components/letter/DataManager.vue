<template>
  <div>
    <tabsmanager v-if="initialDataReady" :submission="submission" :obligation_type="obligation_type" />
  </div>
</template>

<script>
import tabsManager from '@/components/letter/TabsManager'
import dataManagerMixin from '@/components/common/mixins/DataManagerMixin'

export default {
  name: 'DataManager',
  components: {
    tabsmanager: tabsManager
  },
  mixins: [dataManagerMixin]
}
</script>
