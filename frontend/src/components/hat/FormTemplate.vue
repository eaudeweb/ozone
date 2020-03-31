<template>
  <div v-if="tab_info">
    <div class="form-sections">
      <div class="table-wrapper">
        <div class="table-title mb-2">
          <h4>
            {{tab_info.formNumber}}.1
            <span v-translate>Substances</span>
          </h4>
          <b-btn class="mr-3" variant="outline-danger" @click="bulkRemove(selectedForDelete)" v-if="selectedForDelete.length">
            <span><span v-translate>Delete</span>&nbsp;{{selectedForDelete.length}}&nbsp;<span v-translate>selected rows</span></span>
          </b-btn>
          <div v-show="table.tableFilters" class="table-filters">
            <b-input-group :prepend="$gettext('Filter')">
              <b-form-input  :class="{ highlighted: table.filters.search && table.filters.search.length }"  v-model="table.filters.search"/>
            </b-input-group>
          </div>
          <i @click="table.tableFilters = !table.tableFilters" class="fa fa-filter fa-lg"></i>
        </div>

        <b-table
          show-empty
          outlined
          bordered
          hover
          head-variant="light"
          stacked="md"
          class="submission-table full-bordered"
          :items="tableItems"
          :fields="tableFields"
          :current-page="table.currentPage"
          :per-page="table.perPage"
          :sort-by.sync="table.sortBy"
          :sort-desc.sync="table.sortDesc"
          :sort-direction="table.sortDirection"
          :empty-text="tableEmptyText"
          :filter="table.filters.search"
          ref="table"
        >
          <template v-for="field in tableFields" v-slot:[`head(${field.key})`]="field">
            <div :style="`width: ${field.width ? field.width + 'px' : 'auto'}`" v-html="field.label" :key="field.key"></div>
          </template>
          <template v-slot:thead-top>
            <tr class="first-header">
              <th
                v-for="(header, header_index) in tab_info.section_headers"
                :colspan="header.colspan"
                :key="header_index"
              >
                <div
                  v-if="header.tooltip"
                  v-b-tooltip.hover
                  placement="left"
                  :title="header.tooltip"
                >
                  <span v-html="header.label"></span>
                  <i class="fa fa-info-circle fa-lg"></i>
                </div>
                <div v-else>
                  <span v-html="header.label"></span>
                </div>
              </th>
            </tr>
          </template>
          <template v-slot:cell(checkForDelete)="cell">
            <fieldGenerator
              v-show="$store.getters.can_edit_data && $store.getters.edit_mode"
              :fieldInfo="{index:cell.item.index,tabName: tabName, field:'checkForDelete'}"
              :field="cell.item.originalObj.checkForDelete"
            />
          </template>
          <template v-slot:cell(group)="cell">
            <div class="group-cell">{{cell.item.group}}</div>
          </template>
          <template v-slot:cell(substance)="cell">
            <div class="substance-blend-cell">{{cell.item.substance}}</div>
          </template>
          <template v-for="inputField in getTabInputFields" v-slot:[`cell(${inputField})`]="cell">
            <fieldGenerator
              :key="`${cell.item.index}_${inputField}_${tabName}`"
              :fieldInfo="{index:cell.item.index,tabName: tabName, field:inputField}"
              :disabled="['remarks_os', 'remarks_party'].includes(inputField) ? getCommentFieldPermission(inputField) : !$store.getters.edit_mode"
              :field="cell.item.originalObj[inputField]"
            ></fieldGenerator>
          </template>
          <template v-slot:cell(validation)="cell">
            <b-btn-group class="row-controls">
              <span  @click="createModalData(cell.item.originalObj, cell.item.index)">
               <i
                  :class="{
                    'fa-pencil-square-o': $store.getters.can_edit_data && $store.getters.edit_mode,
                    'fa-eye': !$store.getters.can_edit_data || !$store.getters.edit_mode,
                    'fa fa-lg': true
                  }"
                  :title="($store.getters.can_edit_data && $store.getters.edit_mode) ? $gettext('Edit') : $gettext('View')"
                  v-b-tooltip
                ></i>
              </span>
              <span
                v-if="$store.getters.can_edit_data && $store.getters.edit_mode"
                @click="remove_field(cell.item.index)"
                class="table-btn"
              >
                <i class="fa fa-trash fa-lg" v-b-tooltip :title="$gettext('Delete')"></i>
              </span>
              <ValidationLabel
                :open-validation-callback="openValidation"
                :validation="cell.item.originalObj.validation.selected"
                :index="cell.item.index"
              />
            </b-btn-group>
          </template>
        </b-table>
      </div>

      <div v-if="hasBlends" class="table-wrapper">
        <div class="table-title">
          <h4>
            {{tab_info.formNumber}}.2
            <span v-translate>Mixtures</span>
          </h4>
          <b-btn class="mr-3" variant="outline-danger" @click="bulkRemove(selectedForDeleteBlends)" v-if="selectedForDeleteBlends.length">
            <span><span v-translate>Delete</span>&nbsp;{{selectedForDeleteBlends.length}}&nbsp;<span v-translate>selected rows</span></span>
          </b-btn>
          <div v-show="tableBlends.tableFilters" class="table-filters">
            <b-input-group :prepend="$gettext('Filter')">
              <b-form-input  :class="{ highlighted: tableBlends.filters.search && tableBlends.filters.search.length }"  v-model="tableBlends.filters.search"/>
            </b-input-group>
          </div>
          <i
            @click="tableBlends.tableFilters = !tableBlends.tableFilters"
            class="fa fa-filter fa-lg"
          ></i>
        </div>

        <b-table
          show-empty
          outlined
          bordered
          hover
          head-variant="light"
          class="submission-table full-bordered"
          stacked="md"
          :items="tableItemsBlends"
          :fields="tableFieldsBlends"
          :current-page="tableBlends.currentPage"
          :per-page="tableBlends.perPage"
          :sort-by.sync="tableBlends.sortBy"
          :sort-desc.sync="tableBlends.sortDesc"
          :sort-direction="tableBlends.sortDirection"
          :empty-text="tableBlendsEmptyText"
          :filter="tableBlends.filters.search"
          ref="tableBlends"
        >
          <template v-for="field in tableFieldsBlends" v-slot:[`head(${field.key})`]="field">
            <div v-html="field.label" :key="field.key"></div>
          </template>
          <template v-slot:thead-top>
            <tr class="first-header">
              <th
                v-for="(header, header_index) in tab_info.section_headers"
                :colspan="header.colspan"
                :key="header_index"
              >
                <div
                  v-if="header.tooltip"
                  v-b-tooltip.hover
                  placement="left"
                  :title="header.tooltip"
                >
                  <span v-html="header.label"></span>
                  <i class="fa fa-info-circle fa-lg"></i>
                </div>
                <div v-else>
                  <span v-html="header.label"></span>
                </div>
              </th>
            </tr>
          </template>
          <template v-slot:cell(type)="cell">
            <div
              class="group-cell"
            >{{tab_data.blends.find(blend => cell.item.originalObj.blend.selected === blend.id).type}}</div>
          </template>
          <template v-slot:cell(checkForDelete)="cell">
            <fieldGenerator
              v-show="$store.getters.can_edit_data && $store.getters.edit_mode"
              :fieldInfo="{index:cell.item.index,tabName: tabName, field:'checkForDelete'}"
              :field="cell.item.originalObj.checkForDelete"
            />
          </template>
          <template v-slot:cell(blend)="cell">
            <span
              style="cursor:pointer;"
              class="substance-blend-cell"
              v-b-tooltip.hover="'Click to expand/collapse mixture'"
              @click.stop="cell.toggleDetails"
            >
              <i :class="`fa fa-caret-${expandedStatus(cell.item._showDetails)}`"></i>
              {{cell.item.blend}}
            </span>
          </template>

          <template v-for="inputField in getTabInputFields" v-slot:[`cell(${inputField})`]="cell">
            <fieldGenerator
              :key="`${cell.item.index}_${inputField}_${tabName}`"
              :fieldInfo="{index:cell.item.index,tabName: tabName, field:inputField}"
              :disabled="['remarks_os', 'remarks_party'].includes(inputField) ? getCommentFieldPermission(inputField) : !$store.getters.edit_mode"
              :field="cell.item.originalObj[inputField]"
            ></fieldGenerator>
          </template>

          <template v-slot:cell(validation)="cell">
            <b-btn-group class="row-controls">
              <span  @click="createModalData(cell.item.originalObj, cell.item.index)">
                <i
                    :class="{
                      'fa-pencil-square-o': $store.getters.can_edit_data && $store.getters.edit_mode,
                      'fa-eye': !$store.getters.can_edit_data || !$store.getters.edit_mode,
                      'fa fa-lg': true
                    }"
                    :title="($store.getters.can_edit_data && $store.getters.edit_mode) ? $gettext('Edit') : $gettext('View')"
                    v-b-tooltip
                  ></i>
              </span>
              <span
                v-if="$store.getters.can_edit_data && $store.getters.edit_mode"
                @click="remove_field(cell.item.index)"
                class="table-btn"
              >
                <i class="fa fa-trash fa-lg" v-b-tooltip :title="$gettext('Delete')"></i>
              </span>
              <ValidationLabel
                :open-validation-callback="openValidation"
                :validation="cell.item.originalObj.validation.selected"
                :index="cell.item.index"
              />
            </b-btn-group>
          </template>

          <template v-slot:row-details="row">
            <thead>
              <tr>
                <th
                  class="small"
                  v-for="(header, header_index) in tab_info.blend_substance_headers"
                  :colspan="header.colspan"
                  :key="header_index"
                >
                  <span>{{labels[header]}}</span>
                </th>
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

    <div class="table-wrapper">
      <div
        v-for="(comment, comment_key) in tab_info.comments"
        :key="comment_key"
        class="comments-input"
      >
        <label>
          <span>{{labels[comment_key]}}</span>
        </label>
        <!-- addComment(state, { data, tab, field }) { -->
        <textarea
          @change="$store.commit('addComment', {data: $event.target.value, tab:tabName, field: comment_key})"
          :disabled="getCommentFieldPermission(comment_key)"
          class="form-control"
          :value="comment.selected"
        ></textarea>
      </div>
    </div>

    <hr>

    <div class="footnotes">
      <p v-for="(footnote, footnote_index) in tab_info.footnotes" :key="footnote_index">
        <small>{{footnote}}</small>
      </p>
    </div>

    <AppAside
      v-if="($store.getters.can_edit_data && $store.getters.edit_mode) || validationLength"
      fixed
    >
      <DefaultAside
        v-on:fillSearch="fillTableSearch($event)"
        :parentTabIndex.sync="sidebarTabIndex"
        :hovered="hovered"
        :tabName="tabName"
      ></DefaultAside>
    </AppAside>
  </div>
</template>

<script>
import ValidationLabel from '@/components/common/form-components/ValidationLabel'
import FormTemplateMxin from '@/components/common/mixins/FormTemplateMixin'
import { getLabels } from '@/components/hat/dataDefinitions/labels'

export default {
  mixins: [FormTemplateMxin],
  components: {
    ValidationLabel
  },
  data() {
    return {
      typeOfDisplayObj: {
        substance: 'substances',
        blend: 'blends'
      }
    }
  },
  created() {
    const labels = getLabels(this.$gettext)
    this.labels = {
      ...labels.common,
      ...labels[this.tab_info.name]
    }
  },
  methods: {

  },
  computed: {
    getTabInputFields() {
      return this.tab_info.input_fields
    },
    hasSubstances() {
      return Object.keys(this.$store.state.form.tabs[this.tabName].default_properties).includes('substance')
    },
    hasBlends() {
      return Object.keys(this.$store.state.form.tabs[this.tabName].default_properties).includes('blend')
    },
    tableCounter() {
      const counter = []
      if (this.hasSubstances) counter.push(1)
      if (this.hasBlends) counter.push(1)
      return counter.length
    }
  }
}
</script>
