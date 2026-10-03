<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { api } from './api/client'
import type { EpochPrediction, GradCamResponse, Sample } from './api/data-contracts'
import EpochChart from './components/EpochChart.vue'

const samples = ref<Sample[]>([])
const selected = ref<Sample | null>(null)
const predictions = ref<EpochPrediction[]>([])
const trueLabel = ref('')
const selectedEpoch = ref<number | null>(null)
const hoverEpoch = ref<number | null>(null)
const compareEpoch = computed(() => hoverEpoch.value ?? selectedEpoch.value)
const cam = ref<GradCamResponse | null>(null)
const loading = ref(false)

async function loadMeta() {
  const { data } = await api.samplesApiSamplesGet()
  samples.value = data
}

async function selectSample(sample: Sample) {
  selected.value = sample
  selectedEpoch.value = null
  hoverEpoch.value = null
  cam.value = null
  const { data } = await api.predictionsApiPredictionsIndexGet(sample.index)
  predictions.value = data.predictions
  trueLabel.value = data.true_label
}

let requestId = 0
async function loadGradCam() {
  if (!selected.value || selectedEpoch.value === null) {
    cam.value = null
    return
  }
  const id = ++requestId
  loading.value = true
  try {
    const { data } = await api.gradcamApiGradcamGet({
      index: selected.value.index,
      epoch_a: selectedEpoch.value,
      epoch_b: compareEpoch.value ?? selectedEpoch.value,
    })
    if (id === requestId) cam.value = data
  } finally {
    if (id === requestId) loading.value = false
  }
}

watch([selected, selectedEpoch, compareEpoch], loadGradCam)

const percent = (p: number) => `${(p * 100).toFixed(1)}%`

onMounted(loadMeta)
</script>

<template>
  <main>
    <h1>How They Learn</h1>
    <p class="intro">
      Compare a CIFAR-10 classifier's predictions and Grad-CAM explanations across training epochs.
      Pick an image, then choose two epochs to see what the network learned to look at.
    </p>

    <section>
      <h2>1. Pick an image</h2>
      <div class="gallery">
        <button
          v-for="s in samples"
          :key="s.index"
          class="thumb"
          :class="{ active: selected?.index === s.index }"
          @click="selectSample(s)"
        >
          <img :src="s.thumbnail" :alt="s.label_name" />
          <span>{{ s.label_name }}</span>
        </button>
      </div>
    </section>

    <template v-if="selected">
      <section>
        <h2>2. Prediction confidence over epochs</h2>
        <p>Click an epoch to select it, then hover another epoch to compare.</p>
        <EpochChart
          :predictions="predictions"
          :true-label="trueLabel"
          :selected-epoch="selectedEpoch"
          :compare-epoch="compareEpoch"
          @select="selectedEpoch = $event"
          @hover="hoverEpoch = $event"
        />
      </section>

      <section v-if="selectedEpoch !== null">
        <h2>3. Grad-CAM: what changed between the two epochs?</h2>
        <div v-if="cam" class="cam-grid">
          <figure>
            <img :src="cam.original" alt="original" />
            <figcaption>Original ({{ cam.true_label }})</figcaption>
          </figure>
          <figure>
            <img :src="cam.epoch_a.cam" alt="Grad-CAM epoch A" />
            <figcaption>
              Epoch {{ cam.epoch_a.epoch }} &mdash; predicted {{ cam.epoch_a.predicted_label }}
              ({{ percent(cam.epoch_a.predicted_prob) }})
            </figcaption>
          </figure>
          <figure>
            <img :src="cam.epoch_b.cam" alt="Grad-CAM epoch B" />
            <figcaption>
              Epoch {{ cam.epoch_b.epoch }} &mdash; predicted {{ cam.epoch_b.predicted_label }}
              ({{ percent(cam.epoch_b.predicted_prob) }})
            </figcaption>
          </figure>
          <figure>
            <img :src="cam.diff" alt="difference" />
            <figcaption>Difference (B &minus; A)</figcaption>
          </figure>
        </div>
        <p v-else-if="loading">Computing Grad-CAM&hellip;</p>
      </section>
    </template>
  </main>
</template>

<style scoped>
main {
  max-width: 900px;
  margin: 0 auto;
  padding: 32px 20px 64px;
}

section {
  margin-top: 40px;
}

.gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 8px;
}

.thumb {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  font: inherit;
  color: var(--text);
}
.thumb img {
  width: 64px;
  height: 64px;
  image-rendering: pixelated;
}
.thumb span {
  font-size: 12px;
}
.thumb.active img {
  outline: 2px solid var(--accent);
}

.cam-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 16px;
}
.cam-grid figure {
  margin: 0;
}
.cam-grid img {
  width: 100%;
  image-rendering: pixelated;
}
.cam-grid figcaption {
  font-size: 13px;
}
</style>
