<template>
  <div v-if="tab_info">
    <div class="form-sections">
      <table ref="tableHeader" class="table submission-table header-only">
        <thead>
          <tr class="first-header">
            <th
              v-for="(header, header_index) in tab_info.section_headers"
              :colspan="header.colspan"
              :key="header_index"
            >
              <div v-if="header.tooltip" v-b-tooltip.hover placement="left" :title="header.tooltip">
                <span v-html="header.label"></span>
                <i class="fa fa-info-circle fa-lg"></i>
              </div>
              <div v-else>
                <span v-html="header.label"></span>
              </div>
            </th>
          </tr>
        </thead>
      </table>

      <table ref="tableHeaderBlends" class="table submission-table header-only">
        <thead>
          <tr class="first-header">
            <th
              v-for="(header, header_index) in tab_info.section_headers"
              :colspan="header.colspan"
              :key="header_index"
            >
              <div v-if="header.tooltip" v-b-tooltip.hover placement="left" :title="header.tooltip">
                <span v-html="header.label"></span>
                <i class="fa fa-info-circle fa-lg"></i>
              </div>
              <div v-else>
                <span v-html="header.label"></span>
              </div>
            </th>
          </tr>
        </thead>
      </table>

			<div class="table-wrapper">

				<div class="table-title">
					<h4> {{tab_info.formNumber}}.1 Substances</h4>
					<i @click="table.tableFilters = !table.tableFilters" class="fa fa-filter fa-lg"></i>
				</div>
				<hr>

				<div v-show="table.tableFilters" class="table-filters mb-2">
						<b-input-group prepend="Search">
								<b-form-input v-model="table.filters.search"/>
						</b-input-group>
				</div>

				<b-table
					show-empty
					outlined
					bordered
					@input="tableLoaded"
					@row-hovered="rowHovered"
					hover
					head-variant="light"
					stacked="md"
					class="submission-table"
					:items="tableItems"
					:fields="tableFields"
					:current-page="table.currentPage"
					:per-page="table.perPage"
					:sort-by.sync="table.sortBy"
					:sort-desc.sync="table.sortDesc"
					:sort-direction="table.sortDirection"
					:filter="table.filters.search"
					ref="table"
				>
					<template
						slot="substance"
						slot-scope="cell"
					>
						<div class="table-btn-group">
							<b-btn
								variant="info"
								@click="createModalData(cell.item.originalObj, cell.item.index)"
							>Edit</b-btn>
							<b-btn
								variant="outline-danger"
								@click="remove_field(cell.item.index, cell.item)"
								class="table-btn"
							>Delete</b-btn>
						</div>
						{{cell.item.substance}}
					</template>
					<template v-for="inputField in getTabInputFields" :slot="inputField" slot-scope="cell">
						<fieldGenerator
							:key="`${cell.item.index}_${inputField}_${tabName}`"
							:fieldInfo="{index:cell.item.index,tabName: tabName, field:inputField}"
							:disabled="allowedChanges"
							:field="cell.item.originalObj[inputField]"
						></fieldGenerator>
					</template>

					<template
						slot="validation"
						slot-scope="cell">
						<span class="validation-wrapper">
							<i
								@click="openValidation"
								v-if="cell.item.validation.length"
								style="color: red; cursor: pointer"
								class="fa fa-exclamation fa-lg"
								v-b-tooltip.hover
								title="Click here to see the validation problems"
							></i>
							<i
								v-else
								style="color: green;"
								class="fa fa-check-square-o fa-lg"
								></i>
						</span>
					</template>
				</b-table>
			</div>

			<div class="table-wrapper">
				<div class="table-title">
					<h4> {{tab_info.formNumber}}.2 Blends</h4>
					<i @click="tableBlends.tableFilters = !tableBlends.tableFilters" class="fa fa-filter fa-lg"></i>
				</div>
				<hr>

				<div class="table-filters mb-2">
						<b-input-group prepend="Search">
								<b-form-input v-model="tableBlends.filters.search"/>
						</b-input-group>
				</div>

				<b-table
					show-empty
					outlined
					bordered
					hover
					head-variant="light"
					class="submission-table"
					@input="tableLoadedBlends"
					@row-hovered="rowHovered"
					stacked="md"
					:items="tableItemsBlends"
					:fields="tableFieldsBlends"
					:current-page="tableBlends.currentPage"
					:per-page="tableBlends.perPage"
					:sort-by.sync="tableBlends.sortBy"
					:sort-desc.sync="tableBlends.sortDesc"
					:sort-direction="tableBlends.sortDirection"
					:filter="tableBlends.filters.search"
					ref="tableBlends"
				>
					<template slot="blend" slot-scope="cell">
						<div class="table-btn-group">
							<b-btn
								variant="info"
								@click="createModalData(cell.item.originalObj, cell.item.index)"
							>Edit</b-btn>
							<b-btn
								variant="outline-danger"
								@click="remove_field(cell.item.index, cell.item)"
								class="table-btn"
							>Delete</b-btn>
						</div>
						<span
							style="cursor:pointer;"
							v-b-tooltip.hover="'Click to expand/collapse blend'"
							@click.stop="cell.toggleDetails"
						>
							<i :class="`fa fa-caret-${expandedStatus(cell.item._showDetails)}`"></i>
							{{cell.item.blend}}
						</span>
					</template>
					
					<template v-for="inputField in getTabInputFields" :slot="inputField" slot-scope="cell">
						<fieldGenerator
							:key="`${cell.item.index}_${inputField}_${tabName}`"
							:fieldInfo="{index:cell.item.index,tabName: tabName, field:inputField}"
							:disabled="allowedChanges"
							:field="cell.item.originalObj[inputField]"
						></fieldGenerator>
					</template>

					<template slot="validation" slot-scope="cell">
						<span class="validation-wrapper">
							<i
								@click="openValidation"
								v-if="cell.item.validation.length"
								style="color: red; cursor: pointer"
								class="fa fa-exclamation fa-lg"
								v-b-tooltip.hover
								title="Click here to see the validation problems"
							></i>
							<i v-else style="color: green;" class="fa fa-check-square-o fa-lg"></i>
						</span>
					</template>

					<template slot="row-details" slot-scope="row">
						<thead>
							<tr>
								<th
									class="small"
									v-for="(header, header_index) in tab_info.blend_substance_headers"
									:colspan="header.colspan"
									:key="header_index"
								>{{labels[header]}}</th>
							</tr>
						</thead>
						<tbody>
							<tr
								class="small"
								v-for="(substance, substance_index) in tab_data.display.blends[row.item.originalObj.blend.selected].components"
								:key="substance_index"
							>
								<td>{{substance.component_name}}</td>
								<td>
									<b>{{(substance.percentage * 100).toPrecision(3)}}%</b>
								</td>
								<td v-for="(order, order_index) in blendSubstanceHeaders" :key="order_index">
									<!-- <span v-if="row.item[order]"> -->
									{{splitBlend(row.item[order], substance.percentage)}}
									<!-- </span> -->
								</td>
							</tr>
						</tbody>
					</template>
				</b-table>
			</div>
    </div>
    <div
      v-for="(comment, comment_index) in tab_info.comments"
      :key="comment_index"
      class="comments-input"
    >
      <label>{{comment.label}}</label>
      <textarea class="form-control" v-model="comment.selected"></textarea>
    </div>
    <hr>
    <div class="footnotes">
      <p v-for="(footnote, footnote_index) in tab_info.footnotes" :key="footnote_index">
        <small>{{footnote}}</small>
      </p>
    </div>

    <AppAside v-if="!allowedChanges" fixed>
      <DefaultAside :parentTabIndex.sync="sidebarTabIndex" :hovered="hovered" :tabName="tabName"></DefaultAside>
    </AppAside>

    <b-modal size="lg" ref="edit_modal" id="edit_modal">
      <div v-if="modal_data" slot="modal-title">
        <span
          v-if="modal_data.field.substance.selected"
        >{{tab_data.display.substances[modal_data.field.substance.selected]}}</span>
        <span v-else>{{tab_data.display.blends[modal_data.field.blend.selected].name}}</span>
      </div>
      <div v-if="modal_data">
        <b-row v-if="modal_data.field.substance.selected">
          <b-col>
            <h6>Change substance</h6>
          </b-col>
          <b-col>
            <multiselect
              class="mb-2"
              @input="updateFormField($event, {index:modal_data.index,tabName: tabName, field:'substance'})"
              trackBy="value"
              label="text"
              placeholder="Select substance"
              :value="modal_data.field.substance.selected"
              :options="tab_data.substances"
            ></multiselect>
          </b-col>
        </b-row>
        <div v-for="(order, order_index) in this.tab_info.modal_order" :key="order_index">
          <b-row>
            <b-col>{{labels[order]}}</b-col>
            <b-col>
              <fieldGenerator
                :fieldInfo="{index:modal_data.index,tabName: tabName, field:order}"
                :disabled="allowedChanges"
                v-if="modal_data.field[order].type != 'multiselect'"
                :field="modal_data.field[order]"
              ></fieldGenerator>
              <multiselect
                v-else
                :clear-on-select="true"
                :hide-selected="true"
                :close-on-select="true"
                trackBy="value"
                label="text"
                placeholder="Countries"
                @input="updateFormField($event, {index:modal_data.index,tabName: tabName, field:order})"
                :value="modal_data.field[order].selected"
                :options="tab_data.countryOptions"
              ></multiselect>
            </b-col>
          </b-row>
          <hr>
        </div>
        <div>
          <b-row
            class="mb-3"
            v-if="fieldsDecisionQuantity"
            v-for="(order,order_index) in fieldsDecisionQuantity"
            :key="order_index"
            v-show="anotherSpecialCase(order, modal_data)"
          >
            <b-col lg="4" class="mb-2">
              <span>{{labels[`decision_${order}`]}}:</span>
            </b-col>
            <b-col lg="4">
              <b-input-group class="modal-group" :prepend="labels['quantity']">
                <fieldGenerator
                  :fieldInfo="{index:modal_data.index,tabName: tabName, field:`quantity_${order}`}"
                  :disabled="allowedChanges"
                  :field="modal_data.field[`quantity_${order}`]"
                ></fieldGenerator>
              </b-input-group>
            </b-col>
            <b-col lg="4">
              <b-input-group class="modal-group" :prepend="labels['decision']">
                <fieldGenerator
                  :fieldInfo="{index:modal_data.index,tabName: tabName, field:`decision_${order}`}"
                  :disabled="allowedChanges"
                  :field="modal_data.field[`decision_${order}`]"
                ></fieldGenerator>
              </b-input-group>
            </b-col>
          </b-row>
          <hr>
        </div>
        <b-row
          class="mt-3"
          v-for="comment_field in ['remarks_os','remarks_party']"
          :key="comment_field"
        >
          <b-col lg="3">
            <h6>{{labels[comment_field]}}</h6>
          </b-col>
          <b-col lg="9">
            <textarea class="form-control" v-model="modal_data.field[comment_field].selected"></textarea>
          </b-col>
        </b-row>
      </div>
      <div slot="modal-footer">
          <div class="modal-footer-info">
            The values are saved as you type
          </div>
          <b-btn @click="$refs.edit_modal.hide()" variant="success">Close modal</b-btn>
      </div>
    </b-modal>
  </div>
</template>

<script>
import FormTemplateMxin from '@/components/common/mixins/FormTemplateMixin'

export default {
	mixins: [FormTemplateMxin],
	components: {
	},
	data() {
		return {
			typeOfDisplayObj: {
				substance: 'substances',
				blend: 'blends'
			}
		}
	},
	methods: {
	},
	computed: {

	}
}
</script>