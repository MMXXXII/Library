<script setup>
import { onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../stores/userStore'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const username = ref('')
const password = ref('')

onMounted(async () => {
  await userStore.fetchUserInfo()
})

async function handleLogin() {
  await userStore.login(username.value, password.value)
  router.replace('/books')
}

async function handleLogout() {
  await userStore.logout()
  router.replace('/login')
}
</script>

<template>
  <v-container v-if="$route.path === '/profile'">
    <v-card>
      <v-card-title>Профиль пользователя</v-card-title>
      <v-card-text>
        <v-progress-linear v-if="userStore.loading" indeterminate></v-progress-linear>

        <div v-else-if="userStore.user">
          <v-list>
            <v-list-item>
              <v-list-item-content>
                <v-list-item-title>Имя пользователя: {{ userStore.user.username }}</v-list-item-title>
              </v-list-item-content>
            </v-list-item>
            <v-list-item>
              <v-list-item-content>
                <v-list-item-title>Email: {{ userStore.user.email }}</v-list-item-title>
              </v-list-item-content>
            </v-list-item>
          </v-list>
          <v-btn @click="handleLogout">Выход</v-btn>
        </div>

        <v-alert v-else-if="userStore.error">
          {{ userStore.error }}
        </v-alert>
      </v-card-text>
    </v-card>
  </v-container>

  <v-container v-else>
    <v-card>
      <v-form @submit.prevent="handleLogin">
        <v-text-field
          label="Имя пользователя"
          v-model="username"
          required
          autocomplete="username"
        ></v-text-field>

        <v-text-field
          label="Пароль"
          v-model="password"
          required
          type="password"
          autocomplete="current-password"
        ></v-text-field>

        <v-btn 
          type="submit" 
          :loading="userStore.loading" 
          :disabled="userStore.loading"
        >
          Войти
        </v-btn>

        <v-alert v-if="userStore.error">
          {{ userStore.error }}
        </v-alert>
      </v-form>
    </v-card>
  </v-container>
</template>
