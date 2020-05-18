import { expect } from 'chai'
import getters from '@/store/getters'

describe('store getters', () => {
  describe('edit_mode', () => {
    const { edit_mode } = getters
    it('missing permissions.form', () => {
      const state = {
        permissions: {
          form: null
        }
      }
      expect(edit_mode(state)).to.be.null
    })
    it('value is equal to permissions.form.edit_mode', () => {
      const state = {
        permissions: {
          form: {
            edit_mode: true
          }
        }
      }
      expect(edit_mode(state)).to.be.true
      state.permissions.form.edit_mode = false
      expect(edit_mode(state)).to.be.false
    })
  })
})
