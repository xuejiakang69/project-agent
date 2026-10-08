import { reactive } from 'vue'
import {
  clearSession,
  login as loginRequest,
  readSession,
  register as registerRequest,
  updateProfile as updateProfileRequest,
} from '@/api/auth'

const state = reactive({
  user: readSession(),
})

export function useAuthStore() {
  async function login(payload) {
    state.user = await loginRequest(payload)
    return state.user
  }

  async function register(payload) {
    return registerRequest(payload)
  }

  async function updateProfile(payload) {
    state.user = await updateProfileRequest(payload)
    return state.user
  }

  function logout() {
    clearSession()
    state.user = null
  }

  return {
    state,
    login,
    register,
    updateProfile,
    logout,
  }
}