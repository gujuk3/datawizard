import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors } from '../theme';

export default function ErrorMessage({ message }) {
  if (!message) return null;
  return (
    <View style={styles.container}>
      <Text style={styles.text}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#ffeaa7',
    borderLeftWidth: 4,
    borderLeftColor: colors.danger,
    padding: 12,
    borderRadius: 6,
    marginVertical: 8,
  },
  text: { color: colors.dark, fontSize: 14 },
});
