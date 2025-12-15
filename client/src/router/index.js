import { createRouter, createWebHistory } from "vue-router"
import Genres from "../components/Genres.vue"
import Libraries from "../components/Libraries.vue"
import Books from "../components/Books.vue"
import Members from "../components/Members.vue"
import Loans from "../components/Loans.vue"
import Profile from "../components/Profile.vue"
import Login from "../components/Login.vue"
import NotFound from '../components/NotFound.vue'
import NoAccess from '../components/NoAccess.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { 
      path: "/", 
      redirect: "/books" 
    },
    { 
      path: "/genres", 
      component: Genres
    },
    { 
      path: "/libraries", 
      component: Libraries
    },
    { 
      path: "/books", 
      component: Books
    },
    { 
      path: "/members", 
      component: Members
    },
    { 
      path: "/loans", 
      component: Loans
    },
    { 
      path: "/profile", 
      component: Profile
    },
    { 
      path: "/login", 
      component: Login 
    },
    { 
      path: "/no-access", 
      component: NoAccess
    },
    { 
      path: '/:pathMatch(.*)*', 
      name: 'NotFound', 
      component: NotFound
    }
  ]
})

export default router