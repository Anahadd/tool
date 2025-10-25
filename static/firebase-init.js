// Firebase initialization and configuration
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import { getAuth, GoogleAuthProvider, signInWithPopup, signOut, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";
import { getStorage, ref, uploadBytes, getDownloadURL, deleteObject } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-storage.js";
import { getFirestore, collection, doc, setDoc, getDoc, updateDoc, addDoc, getDocs, query, where, orderBy } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js";

// Your web app's Firebase configuration
// NOTE: These are client-side keys and are safe to expose
// Real security comes from Firebase Security Rules
const firebaseConfig = {
  apiKey: "AIzaSyCgFWyeom2gwxl0sKLspemus_FFRnT986o",
  authDomain: "kalshitool.firebaseapp.com",
  projectId: "kalshitool",
  storageBucket: "kalshitool.firebasestorage.app",
  messagingSenderId: "209974454501",
  appId: "1:209974454501:web:8cca10724902b1ea164c0c",
  measurementId: "G-KR5DC9607N"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const storage = getStorage(app);
const db = getFirestore(app);
const googleProvider = new GoogleAuthProvider();

// Export for use in other modules
window.firebaseAuth = auth;
window.firebaseStorage = storage;
window.firebaseDB = db;
window.firebaseUser = null;

// Auth state observer
onAuthStateChanged(auth, async (user) => {
    window.firebaseUser = user;
    
    if (user) {
        console.log('User signed in:', user.email);
        // Get ID token for API calls
        const idToken = await user.getIdToken();
        // Store token for API requests
        window.firebaseIdToken = idToken;
        
        // Trigger auth status check in main app
        if (window.onFirebaseAuthChanged) {
            window.onFirebaseAuthChanged(user);
        }
    } else {
        console.log('User signed out');
        window.firebaseIdToken = null;
        
        if (window.onFirebaseAuthChanged) {
            window.onFirebaseAuthChanged(null);
        }
    }
});

// Export Firestore functions
window.firebase = {
    // Firestore functions
    collection,
    doc,
    getDoc,
    getDocs,
    setDoc,
    updateDoc,
    addDoc,
    query,
    where,
    orderBy,
    
    // Auth functions
    signInWithGoogle: async () => {
        const result = await signInWithPopup(auth, googleProvider);
        const user = result.user;
        
        // Store/update user data in Firestore
        const userRef = doc(db, 'users', user.uid);
        const userDoc = await getDoc(userRef);
        
        if (!userDoc.exists()) {
            // First time sign-in, create user profile
            await setDoc(userRef, {
                email: user.email,
                username: user.displayName || user.email.split('@')[0],
                photo_url: user.photoURL,
                created_at: new Date(),
                last_login: new Date()
            });
        } else {
            // Update last login
            await updateDoc(userRef, {
                last_login: new Date()
            });
        }
        
        return user;
    },
    
    logout: async () => {
        await signOut(auth);
    },
    
    getCurrentUser: () => {
        return auth.currentUser;
    },
    
    getIdToken: async () => {
        const user = auth.currentUser;
        if (user) {
            return await user.getIdToken();
        }
        return null;
    },
    
    // Storage functions
    uploadCredentials: async (file) => {
        const user = auth.currentUser;
        if (!user) throw new Error('Not authenticated');
        
        const storageRef = ref(storage, `credentials/${user.uid}/credentials.json`);
        await uploadBytes(storageRef, file);
        
        // Store metadata in Firestore
        await setDoc(doc(db, 'user_credentials', user.uid), {
            has_credentials: true,
            filename: file.name,
            uploaded_at: new Date(),
            storage_path: `credentials/${user.uid}/credentials.json`
        }, { merge: true });
        
        return true;
    },
    
    getCredentialsDownloadURL: async () => {
        const user = auth.currentUser;
        if (!user) throw new Error('Not authenticated');
        
        const storageRef = ref(storage, `credentials/${user.uid}/credentials.json`);
        try {
            const url = await getDownloadURL(storageRef);
            return url;
        } catch (error) {
            if (error.code === 'storage/object-not-found') {
                return null;
            }
            throw error;
        }
    },
    
    hasCredentials: async () => {
        const user = auth.currentUser;
        if (!user) return false;
        
        const docRef = doc(db, 'user_credentials', user.uid);
        const docSnap = await getDoc(docRef);
        
        if (docSnap.exists()) {
            return docSnap.data().has_credentials || false;
        }
        return false;
    },
    
    deleteCredentials: async () => {
        const user = auth.currentUser;
        if (!user) throw new Error('Not authenticated');
        
        const storageRef = ref(storage, `credentials/${user.uid}/credentials.json`);
        await deleteObject(storageRef);
        
        // Update Firestore
        await updateDoc(doc(db, 'user_credentials', user.uid), {
            has_credentials: false
        });
    },
    
    // Firestore functions
    savePreferences: async (preferences) => {
        const user = auth.currentUser;
        if (!user) throw new Error('Not authenticated');
        
        await setDoc(doc(db, 'users', user.uid), {
            preferences: {
                ...preferences,
                updated_at: new Date()
            }
        }, { merge: true });
    },
    
    getPreferences: async () => {
        const user = auth.currentUser;
        if (!user) return null;
        
        const docRef = doc(db, 'users', user.uid);
        const docSnap = await getDoc(docRef);
        
        if (docSnap.exists()) {
            return docSnap.data().preferences || {};
        }
        return {};
    },
    
    getUserData: async () => {
        const user = auth.currentUser;
        if (!user) return null;
        
        const docRef = doc(db, 'users', user.uid);
        const docSnap = await getDoc(docRef);
        
        if (docSnap.exists()) {
            return docSnap.data();
        }
        return null;
    },
    
    storeOAuthToken: async (tokenData) => {
        const user = auth.currentUser;
        if (!user) throw new Error('Not authenticated');
        
        await setDoc(doc(db, 'user_credentials', user.uid), {
            oauth_token: tokenData,
            oauth_updated_at: new Date()
        }, { merge: true });
    },
    
    getOAuthToken: async () => {
        const user = auth.currentUser;
        if (!user) return null;
        
        const docRef = doc(db, 'user_credentials', user.uid);
        const docSnap = await getDoc(docRef);
        
        if (docSnap.exists()) {
            return docSnap.data().oauth_token || null;
        }
        return null;
    }
};

console.log('✅ Firebase initialized');

