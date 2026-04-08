<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../stores/userStore'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const username = ref('')
const password = ref('')
const error = ref('')

onMounted(async () => {
  await userStore.fetchUserInfo()
})

async function handleLogout() {
  await userStore.logout()
  router.replace('/login')
}
</script>

<template>
  <div class="container mt-5">
    <div v-if="route.path === '/profile'">
      <div class="card mx-auto" style="max-width: 400px;">
        <div class="card-header">Профиль пользователя</div>
        <div class="card-body">
          <div v-if="userStore.loading" class="mb-3">
            <div class="progress">
              <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 100%"></div>
            </div>
          </div>

          <div v-else-if="userStore.user">
            <p><strong>Имя пользователя:</strong> {{ userStore.user.username }}</p>
            <p><strong>Email:</strong> {{ userStore.user.email }}</p>
            <button class="btn btn-danger" @click="handleLogout">Выход</button>
          </div>

          <div v-else-if="userStore.error" class="alert alert-danger">
            {{ userStore.error }}
          </div>
        </div>
      </div>
    </div>

    <div v-else>
      <div class="card mx-auto" style="max-width: 400px;">
        <div class="card-header">Вход в систему</div>
        <div class="card-body">
          <form @submit.prevent="handleLogin">
            <div class="mb-3">
              <label for="username" class="form-label">Имя пользователя</label>
              <input type="text" id="username" class="form-control" v-model="username" required autocomplete="username">
            </div>

            <div class="mb-3">
              <label for="password" class="form-label">Пароль</label>
              <input type="password" id="password" class="form-control" v-model="password" required autocomplete="current-password">
            </div>

            <button type="submit" class="btn btn-primary w-100" :disabled="userStore.loading">
              {{ userStore.loading ? 'Загрузка...' : 'Войти' }}
            </button>

            <div v-if="error" class="alert alert-danger mt-3">
              {{ error }}
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
