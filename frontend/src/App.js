// src/App.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LogIn, User, ShoppingCart, Loader2, RefreshCw } from 'lucide-react';

const API_BASE_URL = 'http://127.0.0.1:8000';

// Create a custom axios instance with a request interceptor
// This ensures that the Authorization header is automatically
// included in every request if a token exists in localStorage.
const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);


function App() {

  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [plans, setPlans] = useState([]);
  const [subscription, setSubscription] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [currentPage, setCurrentPage] = useState('login'); // 'login', 'plans', 'dashboard'

  useEffect(() => {
    const savedToken = localStorage.getItem('authToken');
    if (savedToken) {
      setToken(savedToken);
      fetchUserData(savedToken);
    }
  }, []);

  // This useEffect now includes the polling logic and checks for both token and user
  useEffect(() => {
    let intervalId = null;
    if (token && user) {
      // Immediately fetch data when the user logs in
      fetchSubscriptionStatus();
      fetchPlans();

      // Set up an interval to fetch subscription status every 10 seconds
      intervalId = setInterval(() => {
        console.log("Polling for subscription status...");
        fetchSubscriptionStatus();
      }, 10000); // Poll every 10 seconds
    }

    // This is the cleanup function that will clear the interval
    // when the component unmounts or the token or user changes.
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [token, user]);


  const fetchUserData = async (authToken) => {
    try {
      // The custom api instance already handles the Authorization header.
      const response = await api.get('/api/user/');
      setUser(response.data);
      setCurrentPage('plans');
    } catch (error) {
      console.error('Failed to fetch user data', error);
      localStorage.removeItem('authToken');
      setToken(null);
    }
  };

  const fetchPlans = async () => {
    try {
      const response = await api.get('/api/plans/');
      setPlans(response.data);
    } catch (error) {
      console.error('Failed to fetch plans', error);
      setMessage('Failed to load plans.');
    }
  };

  const fetchSubscriptionStatus = async () => {
    setIsLoading(true);
    // Conditional check for user.id to prevent errors
    if (!user || !user.id) {
      setIsLoading(false);
      return;
    }

    try {
      // Corrected URL to match the backend configuration
      const response = await api.get(`/api/users/${user.id}/subscriptions/`);
      if (response.data.length > 0) {
        // Sort subscriptions by end date to ensure we get the most recent one
        const latestSub = response.data.sort((a, b) => new Date(b.end_date) - new Date(a.end_date))[0];
        setSubscription(latestSub);
        setCurrentPage('dashboard');
      } else {
        setSubscription(null);
        setCurrentPage('plans');
      }
    } catch (error) {
      console.error('Failed to fetch subscription status', error);
      setMessage('Failed to fetch subscription status.');
      setSubscription(null);
      setCurrentPage('plans');
    } finally {
      setIsLoading(false);
    }
  };


  const handleLogin = async (username, password) => {
    setIsLoading(true);
    try {
      // The login endpoint doesn't require a token yet, so we use the base axios instance
      const response = await axios.post(`${API_BASE_URL}/api/token/`, { username, password });
      const { token } = response.data;
      setToken(token);
      localStorage.setItem('authToken', token);
      fetchUserData(token);
    } catch (error) {
      setMessage('Login failed. Please check your credentials.');
      console.error('Login error', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    setSubscription(null);
    localStorage.removeItem('authToken');
    setCurrentPage('login');
  };

  const handlePurchase = async (planId) => {
    setIsLoading(true);
    setMessage('');
    try {
      // Use the custom api instance for the request
      await api.post('/api/purchase/', { plan_id: planId });
      setMessage('Purchase successful! Updating status...');
      // Fetch the subscription status again after a short delay
      setTimeout(() => fetchSubscriptionStatus(), 2000);
    } catch (error) {
      setMessage(`Purchase failed: ${error.response?.data?.error || 'An error occurred.'}`);
      console.error('Purchase error', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRenew = async () => {
    setIsLoading(true);
    setMessage('');
    try {
      // Use the custom api instance for the renew request, which automatically includes the token
      await api.post('/api/renew/');
      setMessage('Renewal successful! Updating status...');
      // Fetch the subscription status again after a short delay
      setTimeout(() => fetchSubscriptionStatus(), 2000);
    } catch (error) {
      setMessage(`Renewal failed: ${error.response?.data?.error || 'An error occurred.'}`);
      console.error('Renewal error', error);
    } finally {
      setIsLoading(false);
    }
  };

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="flex flex-col items-center justify-center p-8">
          <Loader2 className="animate-spin text-indigo-600 h-10 w-10 mb-4" />
          <p className="text-gray-600 font-medium">Loading...</p>
        </div>
      );
    }

    switch (currentPage) {
      case 'login':
        return <LoginForm onLogin={handleLogin} message={message} />;
      case 'plans':
        return <PlansList plans={plans} onPurchase={handlePurchase} message={message} />;
      case 'dashboard':
        return <UserDashboard subscription={subscription} onRenew={handleRenew} message={message} />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6 flex flex-col items-center">
      <header className="w-full max-w-4xl flex justify-between items-center py-4 px-6 bg-white shadow rounded-xl mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Subscription App</h1>
        {token && (
          <div className="flex items-center space-x-4">
            <button onClick={() => setCurrentPage('plans')} className="flex items-center text-gray-600 hover:text-indigo-600 transition">
              <ShoppingCart className="h-5 w-5 mr-1" />
              <span>Plans</span>
            </button>
            <button onClick={() => setCurrentPage('dashboard')} className="flex items-center text-gray-600 hover:text-indigo-600 transition">
              <User className="h-5 w-5 mr-1" />
              <span>Dashboard</span>
            </button>
            <button onClick={handleLogout} className="bg-red-500 text-white font-bold py-2 px-4 rounded-lg shadow-md hover:bg-red-600 transition">
              Logout
            </button>
          </div>
        )}
      </header>
      <div className="w-full max-w-4xl bg-white p-8 rounded-xl shadow-lg border border-gray-200">
        {renderContent()}
      </div>
      {message && (
        <div className="fixed bottom-4 right-4 bg-white p-4 rounded-lg shadow-md border border-gray-200 text-sm">
          <p className="font-medium">{message}</p>
        </div>
      )}
    </div>
  );
}

const LoginForm = ({ onLogin, message }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onLogin(username, password);
  };

  return (
    <div className="flex flex-col items-center">
      <LogIn className="h-12 w-12 text-indigo-600 mb-4" />
      <h2 className="text-2xl font-bold mb-6">Login to Continue</h2>
      <form onSubmit={handleSubmit} className="w-full max-w-sm">
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="username">
            Username
          </label>
          <input
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            id="username"
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </div>
        <div className="mb-6">
          <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="password">
            Password
          </label>
          <input
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline"
            id="password"
            type="password"
            placeholder="********"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        {message && <p className="text-red-500 text-xs italic mb-4 text-center">{message}</p>}
        <div className="flex items-center justify-center">
          <button
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
            type="submit"
          >
            Sign In
          </button>
        </div>
      </form>
    </div>
  );
};

const PlansList = ({ plans, onPurchase, message }) => (
  <div>
    <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">Available Plans</h2>
    {message && <p className="text-red-500 text-xs italic mb-4 text-center">{message}</p>}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {plans.map((plan) => (
        <div key={plan.id} className="bg-white rounded-lg shadow-md p-6 flex flex-col justify-between border border-gray-200">
          <div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">{plan.name}</h3>
            <p className="text-gray-600 mb-4">Price: ${plan.price}</p>
            <p className="text-gray-600">Duration: {plan.duration_months} months</p>
          </div>
          <button
            onClick={() => onPurchase(plan.id)}
            className="w-full mt-4 bg-green-600 text-white font-bold py-2 px-4 rounded-lg shadow-sm hover:bg-green-700 transition-all focus:outline-none"
          >
            Purchase Plan
          </button>
        </div>
      ))}
    </div>
  </div>
);

const UserDashboard = ({ subscription, onRenew, message }) => {
  if (!subscription) {
    return (
      <div className="p-6 text-center">
        <p className="text-gray-600 font-medium">You don't have an active subscription. Please visit the Plans page.</p>
      </div>
    );
  }

  const isActive = subscription.is_active;

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">Your Subscription</h2>
      {message && <p className={`text-center mb-4 ${message.includes('successful') ? 'text-green-600' : 'text-red-600'}`}>{message}</p>}
      <div className="bg-gray-100 rounded-lg p-6 shadow-inner border border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <p className="text-lg font-semibold text-gray-700">Plan:</p>
          <p className="text-lg text-gray-900">{subscription.plan.name}</p>

          <p className="text-lg font-semibold text-gray-700">End Date:</p>
          <p className="text-lg text-gray-900">{subscription.end_date}</p>

          <p className="text-lg font-semibold text-gray-700">Status:</p>
          <p className={`text-lg font-bold ${isActive ? 'text-green-600' : 'text-red-600'}`}>
            {isActive ? 'Active' : 'Inactive'}
          </p>
        </div>
      </div>
      {!isActive && (
        <div className="mt-6 text-center">
          <button
            onClick={onRenew}
            className="bg-indigo-600 text-white font-bold py-3 px-6 rounded-lg shadow-md hover:bg-indigo-700 transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            <RefreshCw className="inline-block h-5 w-5 mr-2" />
            Renew Subscription
          </button>
        </div>
      )}
    </div>
  );
};

export default App;
