<template>
  <div v-if="tabName">
    <div class="container">
      <h3>Add substances</h3>
      <h5>Filter Groups</h5>
      <multiselect @input="prepareSubstances" :multiple="true" label="text" trackBy="value" v-model="selected_groups.selected" :options="selected_groups.options" placeholder="Select annex group(s)"></multiselect>
      <hr>
      <multiselect :clear-on-select="false" :hide-selected="true" :close-on-select="false" class="mb-2" label="text" trackBy="value" :multiple="true" placeholder="Select substance(s)" v-model="selected_substance.selected" @change="updateGroup($event)" :options="selected_substance.options"></multiselect>
      <hr>
      <b-btn @click="addSubstance" variant="success">Add rows</b-btn>
    </div>
  </div>
</template>

<script>

import Multiselect from '@/components/common/modifiedMultiselect'

export default {

	props: {
		tabName: String
	},

	components: {
		Multiselect
	},

	computed: {
		substances() {
			return this.$store.state.initialData.substances
		}
	},

	mounted() {
		this.prepareGroups()
	},

	data() {
		return {

			substancesOptions: [],

			selected_substance: {
				selected: null,
				group: null,
				options: []
			},

			selected_groups: {
				selected: [],
				options: []
			},

			group_field: {
				label: '',
				name: '',
				substance: null
			}
		}
	},

	created() {
	},

	methods: {

		prepareSubstances() {
			this.selected_substance.options = []
			this.substances.forEach(substance => {
				if (this.selected_groups.selected.includes(substance.group.group_id)) {
					this.selected_substance.options.push({ text: substance.text, value: substance.value })
				}
			})
		},

		pushUnique(array, item) {
			if (array.indexOf(item) === -1) {
				array.push(item)
			}
		},

		prepareGroups() {
			const indexOfAll = (arr, val) => arr.reduce((acc, el, i) => (el === val ? [...acc, i] : acc), [])
			const currentGroups = []
			this.substances.forEach(substance => {
				currentGroups.push(substance.group.group_id)
				if (indexOfAll(currentGroups, substance.group.group_id).length <= 1) {
					this.selected_groups.options.push({ text: substance.group.group_id, value: substance.group.group_id })
				}
			})
			this.prepareSubstances()
		},

		updateGroup(selected_substance) {
			this.substances.forEach(substance => {
				if (selected_substance.includes(substance.value)) {
					this.group_field.label = substance.group.group_id
					this.group_field.name = substance.group.group_id
				}
			})
		},

		addSubstance() {
			this.updateGroup(this.selected_substance.selected)
			console.log('group-field', this.group_field)

			this.$store.dispatch('createSubstance', {
				substanceList: this.selected_substance.selected,
				currentSectionName: this.tabName,
				groupName: this.group_field.name,
				country: null,
				blendList: null,
				prefillData: null
			})

			this.resetData()
		},

		resetData() {
			this.selected_substance.selected = null
			this.selected_groups.selected = []
			this.group_field = {
				label: '',
				name: '',
				substance: null
			}
		},

		removeSpecialChars(str) {
			return str.replace(/[^a-zA-Z0-9]+/g, '')
		}
	},

	watch: {
		substances: {
			handler() {
				this.prepareGroups()
			}
		}
	}

}
</script>

<style lang="css" scoped>
</style>