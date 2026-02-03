<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from './stores/userStore'

const router = useRouter()
const userStore = useUserStore()

const handleLogout = async () => {
  await userStore.logout()
  router.push('/login')
}

onMounted(() => {
  userStore.initializePending()
  userStore.fetchUserInfo()
})
</script>

<template>
  <v-app>
    <v-app-bar app color="white" elevation="2">
      <v-btn v-if="userStore.isAuthenticated" color="primary" variant="text" to="/genres">Жанры</v-btn>
      <v-btn v-if="userStore.isAuthenticated" color="primary" variant="text" to="/libraries">Библиотеки</v-btn>
      <v-btn v-if="userStore.isAuthenticated" color="primary" variant="text" to="/books">Книги</v-btn>
      <v-btn v-if="userStore.isAuthenticated && userStore.isSuperUser" color="primary" variant="text" to="/members">Читатели</v-btn>
      <v-btn v-if="userStore.isAuthenticated" color="primary" variant="text" to="/loans">Выдачи</v-btn>

      <v-spacer></v-spacer>

      <v-menu v-if="userStore.isAuthenticated" activator="#profile-menu-btn" location="bottom end">
        <template #activator="{ props }">
          <v-btn color="secondary" variant="text" v-bind="props" id="profile-menu-btn">
            {{ userStore.user?.username || 'Профиль' }}
            <v-icon end>mdi-menu-down</v-icon>
          </v-btn>
        </template>
        <v-list>
          <v-list-item to="/profile" title="Мой профиль" />
          <v-divider />
          <v-list-item @click="handleLogout" class="text-danger" title="Выход" />
        </v-list>
      </v-menu>

      <v-btn v-if="userStore.isAuthenticated" href="/admin" target="_blank" color="primary" variant="text">Админка</v-btn>
    </v-app-bar>

    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

