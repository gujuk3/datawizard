import 'react-native-gesture-handler';
import { StatusBar } from 'expo-status-bar';
import { Provider as PaperProvider } from 'react-native-paper';
import { AuthProvider } from './src/context/AuthContext';
import Navigation from './src/navigation';
import { paperTheme } from './src/theme';

export default function App() {
  return (
    <PaperProvider theme={paperTheme}>
      <AuthProvider>
        <Navigation />
        <StatusBar style="light" />
      </AuthProvider>
    </PaperProvider>
  );
}
