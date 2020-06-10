<template>
  <div class="tab-title">
    <span class="formNumber" v-if="tab.formNumber">({{tab.formNumber}})</span>
    {{$store.getters.getTabTitle(tab.name)}}
    <div v-if="tabStatus === 'saving'" class="spinner">
      <div class="loader"></div>
    </div>
    <i v-if="tabStatus === false" style="color: red;" class="fa fa-exclamation-circle"></i>
    <i v-if="tabStatus === true" style="color: green;" class="fa fa-check-circle"></i>
    <i v-if="tabStatus === 'edited'" class="fa fa-edit"></i>
    <b-badge v-if="tabStatus === null && tabDataLength" variant="primary" sm>
      {{tabDataLength}}
    </b-badge>
    <b-badge
      v-if="tabStatus === null && tab.name === 'questionaire_questions' && questionaireTabs.yesTabs > 0"
      id="questionaire_yes_tabs"
      variant="primary"
      sm
    >
      {{questionaireTabs.yesTabs}}
    </b-badge>
    <b-badge
      v-if="tabStatus === null && tab.name === 'questionaire_questions' && questionaireTabs.noTabs > 0"
      id="questionaire_no_tabs"
      variant="dark"
      sm
    >
      {{questionaireTabs.noTabs}}
    </b-badge>
  </div>
</template>

<script>

export default {
  props: {
    tab: Object
  },
  computed: {
    tabStatus() {
      return this.$store.getters.getTabStatus(this.tab.name)
    },
    tabDataLength() {
      if (this.tab.name === 'files') return this.$store.state.form.tabs[this.tab.name].form_fields.files.length
      return this.$store.state.form.tabs[this.tab.name].form_fields.length
    },
    questionaireTabs() {
      if (this.tab.name === 'questionaire_questions') {
        let yesTabs = 0
        let noTabs = 0
        Object.keys(this.tab.form_fields).forEach(form => {
          if (this.tab.form_fields[form].selected !== null) {
            // eslint-disable-next-line
            this.tab.form_fields[form].selected ? yesTabs++ : noTabs++
          }
        })
        return {
          yesTabs,
          noTabs
        }
      }
      return null
    }
  }
}
</script>

<style>
.spinner {
  z-index: 1;
  display: inline-flex;
  justify-content: center;
  align-items: center;
  margin-left: 5px;
}
.formNumber {
  margin-right: 0.3rem;
}
.loader {
  border: 3px solid #f3f3f3;
  border-radius: 50%;
  border-top: 3px solid blue;
  border-right: 3px solid green;
  border-bottom: 3px solid red;
  border-left: 3px solid pink;
  width: 15px;
  height: 15px;
  -webkit-animation: spin 2s linear infinite; /* Safari */
  animation: spin 2s linear infinite;
}
.tab-title {
  display: flex;
}

.tab-title i {
  margin-left: 5px;
  margin-top: 5px;
}

.tab-title .badge {
    margin-left: 5px;
    margin-top: -3px;
    max-height: 17px;
}
/* Safari */
@-webkit-keyframes spin {
  0% {
    -webkit-transform: rotate(0deg);
  }
  100% {
    -webkit-transform: rotate(360deg);
  }
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

</style>
