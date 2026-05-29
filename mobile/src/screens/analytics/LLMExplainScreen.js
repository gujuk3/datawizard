import React, { useEffect, useState } from 'react';
import { Text, ScrollView, StyleSheet } from 'react-native';
import { getLLMExplain } from '../../api/analytics';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';
import SectionCard from '../../components/SectionCard';
import { colors } from '../../theme';

export default function LLMExplainScreen({ route }) {
  const { dataset } = route.params;
  const [explanation, setExplanation] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getLLMExplain(dataset.id)
      .then((data) => setExplanation(data?.explanation || ''))
      .catch(() => setError('AI açıklaması alınamadı.'))
      .finally(() => setLoading(false));
  }, [dataset.id]);

  if (loading) return <LoadingSpinner />;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <ErrorMessage message={error} />
      <SectionCard title="AI Açıklaması">
        {explanation ? (
          <Text style={styles.explanation}>{explanation}</Text>
        ) : (
          <Text style={styles.empty}>Açıklama mevcut değil.</Text>
        )}
      </SectionCard>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: 12 },
  explanation: { fontSize: 15, color: colors.dark, lineHeight: 24 },
  empty: { color: colors.lightGray, textAlign: 'center', marginTop: 8 },
});
