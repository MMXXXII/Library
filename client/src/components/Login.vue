<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/userStore'

const router = useRouter()
const userStore = useUserStore()

const username = ref('')
const password = ref('')
const error = ref('')

onMounted(async () => {
  await userStore.fetchUserInfo()
  if (userStore.isAuthenticated) {
    router.replace('/books')
  }
})

async function handleLogin() {
  error.value = ''
  await userStore.login(username.value, password.value)
  if (userStore.isAuthenticated) {
    router.replace('/books')
  } else {
    error.value = 'Неверный логин или пароль'
  }
}
</script>

<template>
  <div class="d-flex justify-content-center align-items-center vh-100">
    <div class="card p-4" style="width: 360px;">
      <h5 class="card-title mb-3 text-center">Вход в систему</h5>
      <form @submit.prevent="handleLogin">
        <div class="mb-3">
          <label for="username" class="form-label">Имя пользователя</label>
          <input
            id="username"
            type="text"
            class="form-control"
            v-model="username"
            required
            autocomplete="username"
          >
        </div>

        <div class="mb-3">
          <label for="password" class="form-label">Пароль</label>
          <input
            id="password"
            type="password"
            class="form-control"
            v-model="password"
            required
            autocomplete="current-password"
          >
        </div>

        <button type="submit" class="btn btn-primary w-100">
          Войти
        </button>

        <div v-if="error" class="alert alert-danger mt-3" role="alert">
          {{ error }}
        </div>
      </form>
    </div>
  </div>
</template>
