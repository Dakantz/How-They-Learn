<script setup lang="ts">
import * as d3 from 'd3'
import { onMounted, useTemplateRef, watch } from 'vue'
import type { EpochPrediction } from '../api/data-contracts'

const props = defineProps<{
  predictions: EpochPrediction[]
  trueLabel: string
  selectedEpoch: number | null
  compareEpoch: number | null
}>()

const emit = defineEmits<{
  select: [epoch: number]
  hover: [epoch: number | null]
}>()

const svgRef = useTemplateRef<SVGSVGElement>('svg')

function draw() {
  const svg = d3.select(svgRef.value)
  svg.selectAll('*').remove()
  if (!props.predictions.length) return

  const width = 480
  const height = 220
  const margin = { top: 16, right: 16, bottom: 28, left: 36 }
  const plotTop = margin.top
  const plotBottom = height - margin.bottom

  svg.attr('viewBox', `0 0 ${width} ${height}`)

  const x = d3
    .scaleLinear()
    .domain(d3.extent(props.predictions, (d) => d.epoch) as [number, number])
    .range([margin.left, width - margin.right])

  const y = d3.scaleLinear().domain([0, 1]).range([plotBottom, plotTop])

  svg
    .append('g')
    .attr('transform', `translate(0,${plotBottom})`)
    .call(d3.axisBottom(x).ticks(props.predictions.length).tickFormat(d3.format('d')))

  svg.append('g').attr('transform', `translate(${margin.left},0)`).call(d3.axisLeft(y).ticks(5, '%'))

  const line = (key: 'predicted_prob' | 'true_class_prob') =>
    d3
      .line<EpochPrediction>()
      .x((d) => x(d.epoch))
      .y((d) => y(d[key]))

  svg
    .append('path')
    .datum(props.predictions)
    .attr('fill', 'none')
    .attr('stroke', 'var(--accent)')
    .attr('stroke-width', 2)
    .attr('d', line('true_class_prob'))

  svg
    .append('path')
    .datum(props.predictions)
    .attr('fill', 'none')
    .attr('stroke', 'var(--text)')
    .attr('stroke-width', 2)
    .attr('stroke-dasharray', '4 3')
    .attr('d', line('predicted_prob'))

  const marker = (epoch: number | null, dashed: boolean) => {
    if (epoch === null) return
    svg
      .append('line')
      .attr('x1', x(epoch))
      .attr('x2', x(epoch))
      .attr('y1', plotTop)
      .attr('y2', plotBottom)
      .attr('stroke', 'var(--accent)')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', dashed ? '3 3' : null)
      .attr('opacity', dashed ? 0.6 : 1)
  }
  marker(props.selectedEpoch, false)
  if (props.compareEpoch !== props.selectedEpoch) marker(props.compareEpoch, true)

  // one hit zone per epoch, spanning the full plot height, for click/hover
  const step = props.predictions.length > 1 ? x(props.predictions[1].epoch) - x(props.predictions[0].epoch) : width
  svg
    .selectAll('rect.hit')
    .data(props.predictions)
    .join('rect')
    .attr('class', 'hit')
    .attr('x', (d) => x(d.epoch) - step / 2)
    .attr('y', plotTop)
    .attr('width', step)
    .attr('height', plotBottom - plotTop)
    .attr('fill', 'transparent')
    .style('cursor', 'pointer')
    .on('click', (_event, d) => emit('select', d.epoch))
    .on('mouseenter', (_event, d) => emit('hover', d.epoch))
    .on('mouseleave', () => emit('hover', null))
}

onMounted(draw)
watch(() => [props.predictions, props.selectedEpoch, props.compareEpoch], draw)
</script>

<template>
  <div class="epoch-chart">
    <svg ref="svg"></svg>
    <p class="legend">
      <span class="accent">true class ({{ trueLabel }})</span>
      <span>predicted class</span>
    </p>
  </div>
</template>

<style scoped>
.epoch-chart svg {
  width: 100%;
  height: auto;
}
.legend {
  display: flex;
  gap: 16px;
  font-size: 13px;
}
.legend .accent {
  color: var(--accent);
}
</style>
