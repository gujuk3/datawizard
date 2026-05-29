import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { ActivityIndicator, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { useAuth } from '../context/AuthContext';
import { colors } from '../theme';

import LoginScreen from '../screens/auth/LoginScreen';
import RegisterScreen from '../screens/auth/RegisterScreen';
import ForgotPasswordScreen from '../screens/auth/ForgotPasswordScreen';

import DatasetListScreen from '../screens/datasets/DatasetListScreen';
import DatasetDetailScreen from '../screens/datasets/DatasetDetailScreen';
import UploadDatasetScreen from '../screens/datasets/UploadDatasetScreen';

import AnalyticsHomeScreen from '../screens/analytics/AnalyticsHomeScreen';
import StatisticsScreen from '../screens/analytics/StatisticsScreen';
import CorrelationScreen from '../screens/analytics/CorrelationScreen';
import MissingValuesScreen from '../screens/analytics/MissingValuesScreen';
import LLMExplainScreen from '../screens/analytics/LLMExplainScreen';

import ModelListScreen from '../screens/models/ModelListScreen';
import ModelDetailScreen from '../screens/models/ModelDetailScreen';
import TrainModelScreen from '../screens/models/TrainModelScreen';
import PredictScreen from '../screens/models/PredictScreen';

import AccountScreen from '../screens/account/AccountScreen';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

const stackOptions = {
  headerStyle: { backgroundColor: colors.primary },
  headerTintColor: '#fff',
  headerTitleStyle: { fontWeight: '600' },
};

function DatasetsStack() {
  return (
    <Stack.Navigator screenOptions={stackOptions}>
      <Stack.Screen name="DatasetList" component={DatasetListScreen} options={{ title: 'Veri Setleri' }} />
      <Stack.Screen name="DatasetDetail" component={DatasetDetailScreen} options={{ title: 'Veri Seti' }} />
      <Stack.Screen name="UploadDataset" component={UploadDatasetScreen} options={{ title: 'CSV Yükle' }} />
    </Stack.Navigator>
  );
}

function AnalyticsStack() {
  return (
    <Stack.Navigator screenOptions={stackOptions}>
      <Stack.Screen name="AnalyticsHome" component={AnalyticsHomeScreen} options={{ title: 'Analiz' }} />
      <Stack.Screen name="Statistics" component={StatisticsScreen} options={{ title: 'İstatistikler' }} />
      <Stack.Screen name="Correlation" component={CorrelationScreen} options={{ title: 'Korelasyon' }} />
      <Stack.Screen name="MissingValues" component={MissingValuesScreen} options={{ title: 'Eksik Değerler' }} />
      <Stack.Screen name="LLMExplain" component={LLMExplainScreen} options={{ title: 'AI Açıklaması' }} />
    </Stack.Navigator>
  );
}

function ModelsStack() {
  return (
    <Stack.Navigator screenOptions={stackOptions}>
      <Stack.Screen name="ModelList" component={ModelListScreen} options={{ title: 'Modeller' }} />
      <Stack.Screen name="ModelDetail" component={ModelDetailScreen} options={{ title: 'Model' }} />
      <Stack.Screen name="TrainModel" component={TrainModelScreen} options={{ title: 'Model Eğit' }} />
      <Stack.Screen name="Predict" component={PredictScreen} options={{ title: 'Tahmin Et' }} />
    </Stack.Navigator>
  );
}

function AccountStack() {
  return (
    <Stack.Navigator screenOptions={stackOptions}>
      <Stack.Screen name="Account" component={AccountScreen} options={{ title: 'Hesabım' }} />
    </Stack.Navigator>
  );
}

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.mediumGray,
        tabBarStyle: { borderTopColor: colors.border },
        tabBarIcon: ({ color, size }) => {
          const icons = {
            'Veri Setleri': 'folder-outline',
            'Analiz': 'bar-chart-outline',
            'Modeller': 'hardware-chip-outline',
            'Hesabım': 'person-outline',
          };
          return <Ionicons name={icons[route.name]} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen name="Veri Setleri" component={DatasetsStack} />
      <Tab.Screen name="Analiz" component={AnalyticsStack} />
      <Tab.Screen name="Modeller" component={ModelsStack} />
      <Tab.Screen name="Hesabım" component={AccountStack} />
    </Tab.Navigator>
  );
}

function AuthStack() {
  return (
    <Stack.Navigator screenOptions={{ ...stackOptions, headerShown: false }}>
      <Stack.Screen name="Login" component={LoginScreen} />
      <Stack.Screen name="Register" component={RegisterScreen} />
      <Stack.Screen name="ForgotPassword" component={ForgotPasswordScreen} />
    </Stack.Navigator>
  );
}

export default function Navigation() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <NavigationContainer>
      {user ? <MainTabs /> : <AuthStack />}
    </NavigationContainer>
  );
}
