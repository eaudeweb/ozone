<template>
  <div>
    <b-modal size="lg" ref="transition_modal" id="transition_modal">
      <Submit :hasVersions="hasVersions" v-if="transition === 'submit'"/>
      <Process v-else-if="transition === 'process'"/>
      <Recall v-else-if="transition === 'recall'"/>
      <Finalize v-else-if="transition === 'finalize'"/>
      <Reinstate v-else-if="transition === 'unrecall_to_finalized'"/>
      <div v-else>
        <p v-translate>You are about to change the state of the submission.</p>
        <p v-translate>Press OK to continue with the submission. Press Cancel to make further changes or corrections.</p>
      </div>
      <div slot="modal-footer">
        <b-btn class="mr-2" @click="$refs.transition_modal.hide()" variant="light">
          <span v-translate>Cancel</span>
        </b-btn>
        <b-btn @click="doTransition" variant="success">Ok</b-btn>
      </div>
    </b-modal>
  </div>
</template>

<script>
import TransitionQuestions from '@/components/common/TransitionQuestions'

export default {
  mixins: [TransitionQuestions],
  methods: {
    doTransition() {
      this.$store.dispatch('triggerSave', {
        action: 'doSubmissionTransition',
        data: {
          $gettext: this.$gettext,
          submission: this.submission,
          transition: this.transition,
          increment_minor: false,
          noModal: true
        }
      })
      this.$refs.transition_modal.hide()
    }
  }
}
</script>

