<script>
import SaveMixin from '@/components/common/mixins/SaveMixin'

export default {
  mixins: [SaveMixin],
  methods: {
    getData(tab) {
      return {
        ...tab,
        form_fields: tab.form_fields.map(form => ({
          ...form,
          use_categories: this.getUseCategories(form.use_categories)
        }))
      }
    },
    getUseCategories(useCategories = []) {
      return useCategories.filter(
        category => category.quantity !== 0
      )
    }
  }
}
</script>
