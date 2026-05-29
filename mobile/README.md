# DataWizard Mobile

React Native (Expo) mobile app for the DataWizard platform.

## Setup

```bash
cd mobile
npm install
```

Create a `.env` file:
```
EXPO_PUBLIC_API_URL=http://192.168.0.27:8000/api
```

Use your machine's LAN IP (not `localhost`) when running on a physical device. For simulators, `localhost` works.

## Running

```bash
npm start          # opens Expo dev tools
npm run ios        # iOS simulator
npm run android    # Android emulator
```

Scan the QR code with the Expo Go app on your phone to run on a real device.

## Features

- JWT authentication (login, register, forgot password)
- CSV dataset management (upload, preview, delete)
- Analytics: statistics, correlation matrix, missing values, AI explanation
- ML models: train, evaluate, predict
