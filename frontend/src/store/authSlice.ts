import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { getUserFromToken, login, register } from '../services/authService';

interface AuthState {
  user: any | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}

const savedToken = localStorage.getItem('token');
const savedUser = getUserFromToken(savedToken);

const initialState: AuthState = {
  user: savedUser,
  token: savedToken,
  isAuthenticated: Boolean(savedToken && savedUser),
  loading: false,
  error: null,
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout: (state) => {
      state.user = null;
      state.token = null;
      state.isAuthenticated = false;
      localStorage.removeItem('token');
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Login cases
      .addCase(login.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, { payload }) => {
        state.loading = false;
        state.user = payload.user;
        state.token = payload.token;
        state.isAuthenticated = true;
        localStorage.setItem('token', payload.token);
      })
      .addCase(login.rejected, (state, { payload }) => {
        state.loading = false;
        state.error = typeof payload === 'string' ? payload : (payload as any)?.message || 'Error de autenticacion';
      })
      // Register cases
      .addCase(register.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(register.fulfilled, (state) => {
        state.loading = false;
        state.error = null;
      })
      .addCase(register.rejected, (state, { payload }) => {
        state.loading = false;
        state.error = payload as string;
      });
  },
});

export const { logout, setError, clearError } = authSlice.actions;
export default authSlice.reducer;
