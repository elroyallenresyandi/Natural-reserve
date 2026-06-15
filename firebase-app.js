/* ======================================================
   FIREBASE INTEGRATION LAYER — Natural Reserve
   Drop-in replacement for localStorage-based storage.
   Uses Firebase Auth (email/password) + Firestore.
====================================================== */

const firebaseConfig = {
  apiKey: "AIzaSyDaQTr1RKse2GxUC5jSHGjoyEZQknkSH4U",
  authDomain: "natural-reserve-885b2.firebaseapp.com",
  projectId: "natural-reserve-885b2",
  storageBucket: "natural-reserve-885b2.firebasestorage.app",
  messagingSenderId: "291422831222",
  appId: "1:291422831222:web:d3036bcd1445c457511557",
  measurementId: "G-HDGSJCBNVK"
};

firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
const db   = firebase.firestore();

/* ── Username -> email mapping ──
   Firebase Auth uses email/password. The app uses usernames.
   We map: username "budi" -> email "budi@naturalreserve.local"
   The real email (if provided at registration) is stored in the user's
   Firestore profile document, not used for login. */
function usernameToEmail(username) {
  return username.toLowerCase().trim() + '@naturalreserve.local';
}

/* ── Wait for auth state to be ready (used on page load) ── */
function nrAuthReady() {
  return new Promise(resolve => {
    const unsub = auth.onAuthStateChanged(user => {
      unsub();
      resolve(user);
    });
  });
}

/* ──────────────────────────────────────────────
   REGISTER
   Creates a Firebase Auth user + a Firestore user doc
   at users/{uid} containing profile fields.
────────────────────────────────────────────── */
async function nrRegister({ username, password, email, firstName, lastName, role }) {
  const authEmail = usernameToEmail(username);
  const cred = await auth.createUserWithEmailAndPassword(authEmail, password);
  const uid = cred.user.uid;

  await db.collection('users').doc(uid).set({
    username: username.toLowerCase(),
    email: email || '',
    firstName: firstName || '',
    lastName: lastName || '',
    phone: '',
    location: '',
    bio: '',
    role: role || 'Operator',
    avatar: null,
    joinDate: new Date().toISOString(),
    loginCount: 1,
  });

  return cred.user;
}

/* ──────────────────────────────────────────────
   LOGIN
────────────────────────────────────────────── */
async function nrLogin(username, password) {
  const authEmail = usernameToEmail(username);
  const cred = await auth.signInWithEmailAndPassword(authEmail, password);

  // Increment login count
  const ref = db.collection('users').doc(cred.user.uid);
  await db.runTransaction(async (t) => {
    const doc = await t.get(ref);
    const cur = doc.exists ? (doc.data().loginCount || 0) : 0;
    t.update(ref, { loginCount: cur + 1 });
  });

  return cred.user;
}

/* ──────────────────────────────────────────────
   LOGOUT
────────────────────────────────────────────── */
async function nrLogout() {
  await auth.signOut();
}

/* ──────────────────────────────────────────────
   GET CURRENT USER PROFILE
   Returns the same shape getCurrentUser() used to return.
────────────────────────────────────────────── */
async function nrGetCurrentUser() {
  const user = auth.currentUser;
  if (!user) return null;

  const doc = await db.collection('users').doc(user.uid).get();
  const data = doc.exists ? doc.data() : {};

  return {
    uid: user.uid,
    username: data.username || user.email.split('@')[0],
    firstName: data.firstName || '',
    lastName: data.lastName || '',
    email: data.email || '',
    phone: data.phone || '',
    location: data.location || '',
    bio: data.bio || '',
    role: data.role || 'Operator',
    avatar: data.avatar || null,
    joinDate: data.joinDate || new Date().toISOString(),
    loginCount: data.loginCount || 1,
  };
}

/* ──────────────────────────────────────────────
   SAVE PROFILE INFO
────────────────────────────────────────────── */
async function nrSaveProfile(uid, fields) {
  await db.collection('users').doc(uid).set(fields, { merge: true });
}

/* ──────────────────────────────────────────────
   AVATAR
   Stored as a base64 data URL directly on the user doc.
   (Firestore doc limit is 1MB, fine for small profile pics.)
────────────────────────────────────────────── */
async function nrSaveAvatar(uid, dataUrl) {
  await db.collection('users').doc(uid).set({ avatar: dataUrl }, { merge: true });
}

/* ──────────────────────────────────────────────
   CHANGE PASSWORD
   Requires re-authentication with current password.
────────────────────────────────────────────── */
async function nrChangePassword(currentPassword, newPassword) {
  const user = auth.currentUser;
  const cred = firebase.auth.EmailAuthProvider.credential(user.email, currentPassword);
  await user.reauthenticateWithCredential(cred);
  await user.updatePassword(newPassword);
}

/* ──────────────────────────────────────────────
   ACTIVITY LOG
   Stored at users/{uid}/activity/{auto-id}, capped to last 50.
────────────────────────────────────────────── */
async function nrLogActivity(uid, type, desc) {
  await db.collection('users').doc(uid).collection('activity').add({
    type, desc, time: new Date().toISOString()
  });
}

async function nrGetActivity(uid) {
  const snap = await db.collection('users').doc(uid).collection('activity')
    .orderBy('time', 'desc').limit(50).get();
  return snap.docs.map(d => d.data());
}

/* ──────────────────────────────────────────────
   HISTORY (daily feeding records)
   Stored at users/{uid}/history/{YYYY-MM-DD}
────────────────────────────────────────────── */
async function nrSaveHistoryEntry(uid, dateKey, entry) {
  await db.collection('users').doc(uid).collection('history').doc(dateKey).set(entry);
}

async function nrLoadHistory(uid) {
  const snap = await db.collection('users').doc(uid).collection('history').get();
  const hist = {};
  snap.forEach(doc => { hist[doc.id] = doc.data(); });
  return hist;
}

async function nrDeleteAllHistory(uid) {
  const snap = await db.collection('users').doc(uid).collection('history').get();
  const batch = db.batch();
  snap.forEach(doc => batch.delete(doc.ref));
  await batch.commit();
}

async function nrDeleteAllActivity(uid) {
  const snap = await db.collection('users').doc(uid).collection('activity').get();
  const batch = db.batch();
  snap.forEach(doc => batch.delete(doc.ref));
  await batch.commit();
}

/* ──────────────────────────────────────────────
   FISH LIST (current tank composition)
   Stored at users/{uid}/data/fishList -> { fish: [...] }
────────────────────────────────────────────── */
async function nrSaveFishList(uid, fishList) {
  await db.collection('users').doc(uid).collection('data').doc('fishList').set({ fish: fishList });
}

async function nrLoadFishList(uid) {
  const doc = await db.collection('users').doc(uid).collection('data').doc('fishList').get();
  return doc.exists ? (doc.data().fish || []) : [];
}

/* ──────────────────────────────────────────────
   SETTINGS
   Stored at users/{uid}/data/settings
────────────────────────────────────────────── */
async function nrSaveSettings(uid, settings) {
  await db.collection('users').doc(uid).collection('data').doc('settings').set(settings);
}

async function nrLoadSettings(uid) {
  const doc = await db.collection('users').doc(uid).collection('data').doc('settings').get();
  return doc.exists ? doc.data() : null;
}
