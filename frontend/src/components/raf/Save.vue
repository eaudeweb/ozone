<script>
import SaveMixin from '@/components/common/mixins/SaveMixin'

export default {
  mixins: [SaveMixin],
  methods: {
    getData(tab) {
      if (tab && tab.form_fields && tab.form_fields.length) {
        return {
          ...tab,
          form_fields: tab.form_fields.map(form => ({
            ...form,
            use_categories: this.getUseCategories(form.use_categories)
          }))
        }
      }
      return tab
    },
    getUseCategories(useCategories = []) {
      return useCategories.filter(
        category => category.quantity !== 0
      )
    }
  }
}
</script>
