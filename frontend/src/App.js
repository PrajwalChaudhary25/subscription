// src/App.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LogIn, User, ShoppingCart, Loader2, RefreshCw } from 'lucide-react';

const API_BASE_URL = 'http://127.0.0.1:8000';

// Create a custom axios instance with a request interceptor
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
  const [currentPage, setCurrentPage] = useState('login'); // 'login', 'plans', 'payment_upload', 'dashboard'

  // State to hold the plan ID for payment upload
  const [selectedPlanId, setSelectedPlanId] = useState(null);

  useEffect(() => {
    const savedToken = localStorage.getItem('authToken');
    if (savedToken) {
      setToken(savedToken);
      fetchUserData(savedToken);
    }
  }, []);

  // This useEffect no longer includes the polling logic. It will only run once
  // when the token or user state changes (e.g., after login).
  useEffect(() => {
    if (token && user) {
      // Fetch data when the user logs in or state changes
      fetchSubscriptionStatus();
      fetchPlans();
    }
  }, [token, user]);


  const fetchUserData = async (authToken) => {
    try {
      const response = await api.get('/api/user/');
      setUser(response.data);
      // The page to show after login is now determined by fetchSubscriptionStatus
    } catch (error) {
      console.error('Failed to fetch user data', error);
      localStorage.removeItem('authToken');
      setToken(null);
      setCurrentPage('login');
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
    if (!user || !user.id) {
      setIsLoading(false);
      return;
    }

    try {
      // Fetch all subscriptions for the user (only shows verified/active history)
      const response = await api.get(`/api/users/${user.id}/subscriptions/`);
      if (response.data.length > 0) {
        // Sort to get the most recent subscription
        const latestSub = response.data.sort((a, b) => new Date(b.end_date) - new Date(a.end_date))[0];
        setSubscription(latestSub);
        
        if (latestSub.status === 'ACTIVE') {
            setCurrentPage('dashboard');
        } else {
            setCurrentPage('dashboard');
        }
      } else {
        setSubscription(null);
        setCurrentPage('plans'); // No subscriptions, show plans
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
      const response = await axios.post(`${API_BASE_URL}/api/token/`, { username, password });
      const { token } = response.data;
      setToken(token);
      localStorage.setItem('authToken', token);
      await fetchUserData(token); // Wait for user data to be fetched
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

  // NEW: handlePurchase function
  const handlePurchase = async (planId) => {
    setIsLoading(true);
    setMessage('');
    try {
      // The purchase endpoint now just validates and returns plan info
      const response = await api.post('/api/purchase/', { plan_id: planId });
      
      // Set the selected plan ID and navigate to the payment upload page
      setSelectedPlanId(planId);
      setCurrentPage('payment_upload');
      setMessage('Please upload payment proof to complete your purchase.');
    } catch (error) {
      setMessage(`Selection failed: ${error.response?.data?.error || 'An error occurred.'}`);
      console.error('Purchase error', error);
    } finally {
      setIsLoading(false);
    }
  };

  // NEW: handlePaymentProofUpload function
  const handlePaymentProofUpload = async (file) => {
      setIsLoading(true);
      setMessage('');
      
      const formData = new FormData();
      formData.append('payment_proof', file);
      formData.append('plan', selectedPlanId);  // Send plan ID instead of subscription ID

      try {
          await api.post('/api/payments/', formData, {
              headers: {
                  // When using FormData, axios automatically sets the Content-Type header to multipart/form-data with the correct boundary.
                  // Explicitly setting it can sometimes cause issues. We'll let axios handle it.
                  // Remove this line: 'Content-Type': 'multipart/form-data',
              },
          });
          setMessage('Payment proof uploaded successfully. Awaiting admin verification.');
          // Reset the selected plan ID as the payment is now created
          setSelectedPlanId(null);
          // Navigate back to plans or dashboard
          setCurrentPage('plans');
      } catch (error) {
          setMessage(`Upload failed: ${error.response?.data?.error || 'An error occurred.'}`);
          console.error('Payment upload error', error);
      } finally {
          setIsLoading(false);
      }
  };

  // The handleRenew function is kept for completeness.
  const handleRenew = async () => {
    setIsLoading(true);
    setMessage('');
    try {
      await api.post('/api/renew/');
      setMessage('Renewal successful! Updating status...');
      // After renewal, we immediately check the new status
      fetchSubscriptionStatus();
    } catch (error) {
      setMessage(`Renewal failed: ${error.response?.data?.error || 'An error occurred.'}`);
      console.error('Renewal error', error);
    } finally {
      setIsLoading(false);
    }
  };

  const renderContent = () => {
    if (isLoading) {
      return <LoadingSpinner />;
    }

    switch (currentPage) {
      case 'login':
        return <LoginForm onLogin={handleLogin} message={message} />;
      case 'plans':
        return <PlansList plans={plans} onPurchase={handlePurchase} message={message} />;
      // NEW: A page for uploading payment proof
      case 'payment_upload':
          return <PaymentUploadForm onUpload={handlePaymentProofUpload} planId={selectedPlanId} message={message} />;
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

  const isActive = subscription.status === 'ACTIVE';
  const isPending = subscription.status === 'PENDING';

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
          <p className={`text-lg font-bold ${isActive ? 'text-green-600' : (isPending ? 'text-yellow-600' : 'text-red-600')}`}>
            {subscription.status}
          </p>
        </div>
      </div>
      {!isActive && !isPending && (
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

const LoadingSpinner = () => (
  <div className="flex flex-col items-center justify-center p-8">
    <Loader2 className="animate-spin text-indigo-600 h-10 w-10 mb-4" />
    <p className="text-gray-600 font-medium">Loading...</p>
  </div>
);

// A component for handling payment proof uploads.
const PaymentUploadForm = ({ onUpload, planId, message }) => {
    const [file, setFile] = useState(null);

    const handleSubmit = (e) => {
      e.preventDefault();
      if (file) {
        onUpload(file);
      }
    };

    return (
      <div className="flex flex-col items-center">
        <h2 className="text-2xl font-bold mb-6 text-center">Upload Payment Proof</h2>
        <p className="text-gray-600 mb-4 text-center">
          Please upload a screenshot or image of your payment. This will be used by an admin to verify your subscription.
        </p>
        {message && <p className="text-red-500 text-xs italic mb-4 text-center">{message}</p>}
        <form onSubmit={handleSubmit} className="w-full max-w-sm">
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="paymentProof">
              Payment Proof
            </label>
            <input
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              id="paymentProof"
              type="file"
              accept="image/*"
              onChange={(e) => setFile(e.target.files[0])}
            />
          </div>
          <div className="flex items-center justify-center">
            <button
              className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:opacity-50 disabled:cursor-not-allowed"
              type="submit"
              disabled={!file}
            >
              Upload Proof
            </button>
          </div>
        </form>
      </div>
    );
  };

export default App;
